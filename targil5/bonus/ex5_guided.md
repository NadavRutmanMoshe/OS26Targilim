# XV6 File System Assignment: File Permissions

## Assignment Overview

**Goal:** Implement a basic file permissions system in XV6 with read, write, and execute permission bits.

---

## Part 1: Add Permission Metadata

### Step 1.1: Modify the On-Disk Structure

**File to edit:** `kernel/fs.h`

**What to do:** Add a `permissions` field to `struct dinode` with padding for alignment

```c
// On-disk inode structure
struct dinode {
  short type;              // File type
  short major;             // Major device number (T_DEVICE only)
  short minor;             // Minor device number (T_DEVICE only)
  short nlink;             // Number of links to inode in file system
  uint size;               // Size of file (bytes)
  uint addrs[NDIRECT+1];   // Data block addresses
  
  short permissions;       // TODO: Add this field - Permission bits (9 bits)
  char pad[60];            // TODO: Add this field - Padding to align to 128 bytes
};
```

**Why padding?** The structure size must divide evenly into the 1024-byte block size. Without padding, you'll get:
```
mkfs: Assertion `(BSIZE % sizeof(struct dinode)) == 0' failed
```

**Permission bit format:**
```
Bits 8-6: Owner permissions (rwx)
Bits 5-3: Group permissions (rwx) - NOT USED in this assignment
Bits 2-0: Other permissions (rwx) - NOT USED in this assignment

For this assignment, only use bits 8-6:
- Bit 8: Read permission    (4 in octal)
- Bit 7: Write permission   (2 in octal)
- Bit 6: Execute permission (1 in octal)

Example: 0700 (octal) = 0b111000000 = rwx------ = full permissions
Example: 0600 (octal) = 0b110000000 = rw------- = read+write only
Example: 0500 (octal) = 0b101000000 = r-x------ = read+execute only
```


---

### Step 1.2: Modify the In-Memory Structure

**File to edit:** `kernel/file.h`

**What to do:** Add the `permissions` field to `struct inode` (NO padding needed here)

```c
// in-memory copy of an inode
struct inode {
  uint dev;           // Device number
  uint inum;          // Inode number
  int ref;            // Reference count
  struct sleeplock lock; // protects everything below here
  int valid;          // inode has been read from disk?

  // Copied from disk:
  short type;         // copy of disk inode
  short major;
  short minor;
  short nlink;
  uint size;
  uint addrs[NDIRECT+1];
  
  short permissions;  // TODO: Add this field - copy of disk inode permissions
                      // Note: Do NOT add padding here - only needed in dinode
};
```

**Why no padding in inode?** The in-memory structure doesn't need to fit into disk blocks, so no alignment constraint.


---

### Step 1.3: Load Permissions from Disk

**File to edit:** `kernel/fs.c`

**Function to modify:** `ilock()`

**What to do:** When loading an inode from disk, copy the `permissions` field

**Find this section in `ilock()`:**
```c
if(ip->valid == 0){
  bp = bread(ip->dev, IBLOCK(ip->inum, sb));
  dip = (struct dinode*)bp->data + ip->inum%IPB;
  ip->type = dip->type;
  ip->major = dip->major;
  ip->minor = dip->minor;
  ip->nlink = dip->nlink;
  ip->size = dip->size;
  memmove(ip->addrs, dip->addrs, sizeof(ip->addrs));
  
  // TODO: Add this line here
  ip->permissions = dip->permissions;
  
  brelse(bp);
  ip->valid = 1;
  if(ip->type == 0)
    panic("ilock: no type");
}
```


---

### Step 1.4: Initialize Permissions When Creating Files

**File to edit:** `kernel/fs.c`

**Function to modify:** `ialloc()`

**What to do:** Set default permissions when a new inode is allocated

**Find this section in `ialloc()`:**
```c
if(dip->type == 0){  // a free inode
  memset(dip, 0, sizeof(*dip));
  dip->type = type;
  
  // TODO: Add this line - default to rwx (0700)
  dip->permissions = 0700;
  
  log_write(bp);
  brelse(bp);
  return iget(dev, inum);
}
```

**Why 0700?** This gives full permissions (read, write, execute) to newly created files. Users can restrict them later with `chmod()`.


---

### Step 1.5: Save Permissions Back to Disk

**File to edit:** `kernel/fs.c`

**Function to modify:** `iupdate()`

**What to do:** When writing an inode back to disk, include the `permissions` field

**Find this section in `iupdate()`:**
```c
void iupdate(struct inode *ip)
{
  struct buf *bp;
  struct dinode *dip;

  bp = bread(ip->dev, IBLOCK(ip->inum, sb));
  dip = (struct dinode*)bp->data + ip->inum%IPB;
  dip->type = ip->type;
  dip->major = ip->major;
  dip->minor = ip->minor;
  dip->nlink = ip->nlink;
  dip->size = ip->size;
  memmove(dip->addrs, ip->addrs, sizeof(ip->addrs));
  
  // TODO: Add this line
  dip->permissions = ip->permissions;
  
  log_write(bp);
  brelse(bp);
}
```


---

## Part 2: Implement System Calls (40 points)

### Step 2.1: Add System Call Numbers

**File to edit:** `kernel/syscall.h`

**What to do:** Add system call numbers for your new functions

```c
// System call numbers
#define SYS_fork    1
#define SYS_exit    2
// ... existing syscalls ...
#define SYS_close  21

// TODO: Add these lines
#define SYS_chmod     22
#define SYS_getperm   23
```

---

### Step 2.2: Register System Calls

**File to edit:** `kernel/syscall.c`

**What to do:** 

1. Add function declarations at the top:
```c

// TODO: Add these declarations
extern uint64 sys_chmod(void);
extern uint64 sys_getperm(void);
```

2. Add entries to the syscalls array:
```c
static int (*syscalls[])(void) = {
// ... existing entries ...
[SYS_close]   sys_close,

// TODO: Add these entries
[SYS_chmod]   sys_chmod,
[SYS_getperm] sys_getperm,
};
```



---

### Step 2.3: Implement `sys_chmod()`

**File to edit:** `kernel/sysfile.c`

**What to do:** Implement the system call to change file permissions

**Add forward declaration at top of file:**
```c
// Forward declaration for helper function
int check_permission(struct inode *ip, int mode);
```

**Then add the function:**
```c
// TODO: Add this entire function

// Change file permissions
// Usage: chmod("filename.txt", 0600)
uint64 sys_chmod(void)
{
  char path[MAXPATH];
  int mode;
  struct inode *ip;
  
  // Get arguments from user space
  if(argstr(0, path, MAXPATH) < 0)
    return -1;
  
  // IMPORTANT: argint() doesn't return an error code in this xv6 version
  argint(1, &mode);
  
  begin_op();
  
  // Look up the file by path
  if((ip = namei(path)) == 0){
    end_op();
    return -1;
  }
  
  ilock(ip);
  
  // Update permissions (only keep lower 9 bits)
  ip->permissions = mode & 0777;
  iupdate(ip);
  
  iunlock(ip);
  iput(ip);
  end_op();
  
  return 0;
}
```

**What this does:**
1. Gets the filename and new permission mode from user
2. Looks up the file's inode
3. Updates the `permissions` field
4. Writes it back to disk


---

### Step 2.4: Implement `sys_getperm()`

**File to edit:** `kernel/sysfile.c`

**What to do:** Implement the system call to read file permissions

```c
// TODO: Add this entire function

// Get file permissions
// Usage: int perm = getperm("filename.txt")
uint64 sys_getperm(void)
{
  char path[MAXPATH];
  struct inode *ip;
  int permissions;
  
  // Get filename argument from user space
  if(argstr(0, path, MAXPATH) < 0)
    return -1;
  
  begin_op();
  
  // Look up the file by path
  if((ip = namei(path)) == 0){
    end_op();
    return -1;
  }
  
  ilock(ip);
  permissions = ip->permissions;
  iunlock(ip);
  
  iput(ip);
  end_op();
  
  return permissions;
}
```

**What this does:**
1. Gets the filename from user
2. Looks up the file's inode
3. Returns the `permissions` field value


---

### Step 2.5: Add User-Space Declarations

**File to edit:** `user/user.h`

**What to do:** Add function prototypes so user programs can call these

```c
// System call prototypes
int fork(void);
int exit(int) __attribute__((noreturn));
// ... existing prototypes ...
int close(int);

// TODO: Add these prototypes
int chmod(char*, int);
int getperm(char*);
```


---

### Step 2.6: Add Assembly Stubs

**File to edit:** `user/usys.pl`

**What to do:** Add entries for the new system calls

```perl
# ... existing entries ...
entry("close");

# TODO: Add these entries
entry("chmod");
entry("getperm");
```


---

### Step 2.7: Update Makefile

**File to edit:** `Makefile`

**What to do:** Add your test programs to the user program list


Add your test programs:
```makefile
UPROGS=\
	$U/_cat\
	# ... existing programs ...
	$U/_zombie\
	$U/_testperm\
	$U/_testexec\
```



---

## Part 3: Enforce Permissions

Now that files have permissions and can be changed, you need to **check** them before allowing operations.

### Helper Function: Check Permissions

**File to edit:** `kernel/sysfile.c`

**What to do:** Create a helper function to check if an operation is allowed

```c
// TODO: Add this helper function

// Check if current process has permission for requested access
// mode: O_RDONLY (0), O_WRONLY (1), or O_RDWR (2)
// Returns: 0 if allowed, -1 if denied
int check_permission(struct inode *ip, int mode)
{
  // Extract owner permissions (bits 8-6)
  int owner_read = (ip->permissions >> 8) & 1;    // bit 8
  int owner_write = (ip->permissions >> 7) & 1;   // bit 7
  
  // IMPORTANT: Use == for comparison, not bitwise &
  // Because O_RDONLY = 0, O_WRONLY = 1, O_RDWR = 2
  
  // Check read permission
  if(mode == O_RDONLY || mode == O_RDWR){
    if(!owner_read)
      return -1;  // Read denied
  }
  
  // Check write permission
  if(mode == O_WRONLY || mode == O_RDWR){
    if(!owner_write)
      return -1;  // Write denied
  }
  
  return 0;  // Permission granted
}
```

**Common Mistake:** Don't use `(mode & O_RDONLY)` - this won't work because `O_RDONLY = 0`!


---

### Step 3.1: Enforce in `sys_open()`

**File to edit:** `kernel/sysfile.c`

**Function to modify:** `sys_open()`

**What to do:** Check permissions before opening a file

Find the section in `sys_open()` after the file is looked up:
```c
if((ip = namei(path)) == 0){
  end_op();
  return -1;
}
ilock(ip);

// TODO: Add permission check here
if(check_permission(ip, omode) < 0){
  iunlockput(ip);
  end_op();
  return -1;
}

// ... rest of function continues ...
```


---

### Step 3.2: Enforce in `sys_exec()` (Execute Permission)

**File to edit:** `kernel/exec.c`

**IMPORTANT - Fix header includes first!** Add these headers at the top in this order:

```c
#include "types.h"
#include "param.h"
#include "memlayout.h"
#include "riscv.h"
#include "spinlock.h"
#include "sleeplock.h"    // Must come before file.h
#include "fs.h"           // Must come before file.h (defines NDIRECT)
#include "proc.h"
#include "file.h"         // Now this will work
#include "defs.h"
#include "elf.h"
```

**Why this order matters:**
- `file.h` needs `struct sleeplock` (from `sleeplock.h`)
- `file.h` needs `NDIRECT` constant (from `fs.h`)

**Then modify the `exec()` function:**

Find the section after the file is opened:
```c
if((ip = namei(path)) == 0){
  end_op();
  return -1;
}
ilock(ip);

// TODO: Add execute permission check with backwards compatibility
// Allow execution if permissions = 0 (old files) OR if execute bit is set
int owner_exec = (ip->permissions >> 6) & 1;  // bit 6
if(ip->permissions != 0 && !owner_exec){
  iunlockput(ip);
  end_op();
  return -1;
}

// ... rest of function continues ...
```

**Why backwards compatibility?** Existing files (like `/init`) have permissions = 0. Without this check, the system won't boot!


---


## Submission Checklist

### Required Files

- [ ] `kernel/fs.h` - Modified `struct dinode`
- [ ] `kernel/file.h` - Modified `struct inode`
- [ ] `kernel/fs.c` - Modified `ilock()`, `ialloc()`, `iupdate()`
- [ ] `kernel/syscall.h` - Added system call numbers
- [ ] `kernel/syscall.c` 
- [ ] `kernel/sysfile.c` - Implemented `sys_chmod()`, `sys_getperm()`, `check_permission()`
- [ ] `kernel/exec.c` 
- [ ] `user/user.h` - Added function prototypes
- [ ] `user/usys.pl`
- [ ] `user/testperm.c`
- [ ] `user/testexec.c`
- [ ] `user/testpermedge.c`
- [ ] `user/testpermpersist.c`
- [ ] `user/testpermcomprehensive.c`
- [ ] `user/testpermscenarios.c`
- [ ] `user/runtests.c`
- [ ] `Makefile`

---

