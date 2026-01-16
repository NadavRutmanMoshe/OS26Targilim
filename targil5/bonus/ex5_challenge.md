# XV6 File System Assignment: File Permissions (Challenge Mode)

## Assignment Overview

**Goal:** Implement a basic file permissions system in XV6 with read, write, and execute permission bits.

**Note:** This is the challenge version with minimal guidance. If you want step-by-step instructions, use the guided version (ex5.md).

---

## Requirements

### Part 1: Permission Metadata

Implement a 9-bit permission system using bits 8-6 for owner permissions (rwx):
- Bit 8: Read permission
- Bit 7: Write permission  
- Bit 6: Execute permission

**Your tasks:**

1. **Modify on-disk inode structure** (`kernel/fs.h`)
   - Add a `permissions` field to `struct dinode`
   - Add padding to maintain proper disk block alignment (128 bytes)
   - Without padding, you'll get: `mkfs: Assertion (BSIZE % sizeof(struct dinode)) == 0 failed`

2. **Modify in-memory inode structure** (`kernel/file.h`)
   - Add a `permissions` field to `struct inode`
   - No padding needed for in-memory structures

3. **Load permissions from disk** (`kernel/fs.c`)
   - Modify `ilock()` to copy the permissions field from disk to memory

4. **Initialize permissions for new files** (`kernel/fs.c`)
   - Modify `ialloc()` to set default permissions of 0700 (rwx------)

5. **Save permissions to disk** (`kernel/fs.c`)
   - Modify `iupdate()` to write permissions back to disk

---

### Part 2: System Calls

Implement two new system calls:

**`chmod(char *path, int mode)`** - Change file permissions
- Takes a file path and permission mode (e.g., 0600)
- Updates the file's permission bits
- Masks input to 9 bits (use `& 0777`)
- Returns 0 on success, -1 on error

**`getperm(char *path)`** - Get file permissions
- Takes a file path
- Returns the permission bits
- Returns -1 on error

**Implementation requirements:**

1. **Add system call numbers** (`kernel/syscall.h`)
   - Define `SYS_chmod` and `SYS_getperm`

2. **Register system calls** (`kernel/syscall.c`)
   - Add function declarations (use `uint64` return type, not `int`)
   - Add entries to the syscalls array

3. **Implement system call handlers** (`kernel/sysfile.c`)
   - Implement `sys_chmod()` and `sys_getperm()`
   - Use `argstr()` to get filename argument
   - Use `argint()` to get mode argument (note: doesn't return error code)
   - Use `namei()` to look up files
   - Use `begin_op()`/`end_op()` for transactions
   - Call `iupdate()` after modifying permissions

4. **Add user-space interface** (`user/user.h`, `user/usys.pl`)
   - Add function prototypes
   - Add assembly stubs

5. **Update Makefile**
   - Add test programs to `UPROGS`

---

### Part 3: Permission Enforcement

Implement permission checking for file operations:

**`check_permission(struct inode *ip, int mode)`** - Helper function
- Extract read/write/execute bits from `ip->permissions`
- Check if the requested operation is allowed
- Important: O_RDONLY=0, O_WRONLY=1, O_RDWR=2 (use `==` not `&`)
- Return 0 if allowed, -1 if denied

**Enforce in `sys_open()`** (`kernel/sysfile.c`)
- Call `check_permission()` before allowing file access
- Deny access if permissions don't allow the requested mode

**Enforce in `exec()`** (`kernel/exec.c`)
- Check execute permission (bit 6) before running programs
- **Critical:** Implement backwards compatibility - allow execution if `permissions == 0`
- Without this, the system won't boot (init has permissions = 0)
- **Important:** Fix header includes first:
  - Include `sleeplock.h` before `file.h`
  - Include `fs.h` before `file.h`
  - Otherwise you'll get: `field 'lock' has incomplete type`

---

## Testing

Use the test programs provided in `tester.md`:
- `testperm` - Basic read/write tests (required)
- `testexec` - Execute permission tests (required)
- `testpermedge` - Edge cases (optional)
- `testpermpersist` - Persistence tests (optional)
- `testpermcomprehensive` - All combinations (optional)
- `testpermscenarios` - Real-world scenarios (optional)
- `runtests` - Run all tests (optional)

All tests should show **PASS** status.

---

## Key Implementation Details

### Permission Bit Layout
```
Bit:  8   7   6   5   4   3   2   1   0
      r   w   x   r   w   x   r   w   x
      └───┬───┘   └───┬───┘   └───┬───┘
        Owner      Group      Other
```

Only owner bits (8-6) are used in this assignment.

### Examples
- `0700` (octal) = `0b111000000` = rwx------
- `0600` (octal) = `0b110000000` = rw-------
- `0400` (octal) = `0b100000000` = r--------

### Test Output Format
Tests display permissions in hexadecimal:
- `0x1C0` = 0700 octal = rwx------
- `0x180` = 0600 octal = rw-------
- `0x100` = 0400 octal = r--------
- `0x80` = 0200 octal = -w-------
- `0x40` = 0100 octal = --x------

---

## Common Pitfalls

1. **Using `int` instead of `uint64` for system call return types**
   - System calls must return `uint64` on 64-bit architecture

2. **Wrong permission check logic**
   - Don't use `(mode & O_RDONLY)` - use `mode == O_RDONLY`
   - O_RDONLY is 0, so bitwise AND always fails

3. **Forgetting backwards compatibility in exec()**
   - Must allow execution when `permissions == 0`
   - Otherwise system won't boot

4. **Header include order in exec.c**
   - `sleeplock.h` and `fs.h` must come before `file.h`

5. **Not masking chmod input**
   - Use `mode & 0777` to keep only 9 permission bits

6. **Forgetting padding in dinode**
   - Add `char pad[60];` to align structure to 128 bytes

---

## Submission Checklist

### Required Files
- [ ] `kernel/fs.h` - Modified `struct dinode`
- [ ] `kernel/file.h` - Modified `struct inode`
- [ ] `kernel/fs.c` - Modified `ilock()`, `ialloc()`, `iupdate()`
- [ ] `kernel/syscall.h` - Added system call numbers
- [ ] `kernel/syscall.c` - Registered system calls
- [ ] `kernel/sysfile.c` - Implemented `sys_chmod()`, `sys_getperm()`, `check_permission()`
- [ ] `kernel/exec.c` - Added execute permission check
- [ ] `user/user.h` - Added function prototypes
- [ ] `user/usys.pl` - Added assembly stubs
- [ ] Test files from `tester.md`
- [ ] `Makefile` - Added test programs

### Verification
- [ ] Code compiles without errors
- [ ] XV6 boots successfully
- [ ] `testperm` shows all PASS
- [ ] `testexec` shows all PASS
- [ ] Optional tests pass (for bonus points)

---

## Debugging Tips

**If system won't boot:** Check backwards compatibility in `exec()`

**If permissions not enforced:** Check `check_permission()` logic

**If permissions don't persist:** Check `iupdate()` writes to disk

**If compile errors:** Check return types and header includes

**Add debug prints liberally:**
```c
printf("chmod: path=%s, mode=%o\n", path, mode);
printf("permissions=%x, read=%d, write=%d\n", ...);
```


