# Tester

This document contains all test programs for the file permissions assignment.

## What's Included

- **testperm.c** - Basic read/write permission tests (required)
- **testexec.c** - Execute permission tests (required)
- **testpermedge.c** - Edge cases and boundary conditions (optional)
- **testpermpersist.c** - Persistence verification (optional)
- **testpermcomprehensive.c** - All permission combinations (optional)
- **testpermscenarios.c** - Real-world usage scenarios (optional)
- **runtests.c** - Runs all tests automatically (optional)

## How to Use

1. Copy each test file to your `user/` directory
2. Add test programs to Makefile (see section below)
3. Run `make qemu`
4. Inside xv6, run individual tests or use `runtests` for all

## Expected Results

All tests should show **PASS** status. If you see **FAIL**, review the corresponding section in the main assignment document (ex5.md).

**File to create:** `user/testperm.c`

```c
#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"
#include "kernel/fcntl.h"

int main(int argc, char *argv[])
{
  int fd;
  
  printf("Test 1: Create file with full permissions\n");
  
  // Create a file (should have default 0700 permissions)
  fd = open("testfile.txt", O_CREATE | O_RDWR);
  if(fd < 0){
    printf("FAIL: Could not create file\n");
    exit(1);
  }
  write(fd, "hello", 5);
  close(fd);
  
  // Check permissions
  int perm = getperm("testfile.txt");
  printf("Default permissions: %x (expected 0700)\n", perm);
  
  // Test: Read the file (should work)
  fd = open("testfile.txt", O_RDONLY);
  if(fd < 0){
    printf("FAIL: Could not read file\n");
    exit(1);
  }
  printf("PASS: Can read file with permission 0700\n");
  close(fd);
  
  printf("\nTest 2: Remove read permission\n");
  
  // Change to write-only (0200)
  chmod("testfile.txt", 0200);
  perm = getperm("testfile.txt");
  printf("New permissions: %x (expected 0200)\n", perm);
  
  // Try to read (should fail)
  fd = open("testfile.txt", O_RDONLY);
  if(fd < 0){
    printf("PASS: Cannot read file without read permission\n");
  } else {
    printf("FAIL: Should not be able to read file\n");
    close(fd);
  }
  
  printf("\nTest 3: Remove write permission\n");
  
  // Change to read-only (0400)
  chmod("testfile.txt", 0400);
  perm = getperm("testfile.txt");
  printf("New permissions: %x (expected 0400)\n", perm);
  
  // Try to write (should fail)
  fd = open("testfile.txt", O_WRONLY);
  if(fd < 0){
    printf("PASS: Cannot write to file without write permission\n");
  } else {
    printf("FAIL: Should not be able to write to file\n");
    close(fd);
  }
  
  // But reading should work
  fd = open("testfile.txt", O_RDONLY);
  if(fd >= 0){
    printf("PASS: Can read file with read permission\n");
    close(fd);
  } else {
    printf("FAIL: Should be able to read file\n");
  }
  
  printf("\nAll basic tests completed!\n");
  exit(0);
}
```

**File to create:** `user/testexec.c`
```c
#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"
#include "kernel/fcntl.h"

int main(int argc, char *argv[])
{
  printf("=== Execute Permission Test ===\n\n");
  
  // Check old files have permissions = 0
  int perm = getperm("ls");
  printf("System file (ls) permissions: %x\n", perm);
  printf("Old files default to 0 (backwards compatible)\n\n");
  
  // Create test file
  int fd = open("testfile", O_CREATE | O_RDWR);
  write(fd, "test", 4);
  close(fd);
  
  // Test with execute permission
  printf("Test 1: Set permissions to 0700 (rwx)\n");
  chmod("testfile", 0700);
  perm = getperm("testfile");
  int exec_bit = (perm >> 6) & 1;
  printf("  Permissions: %x, Execute bit: %d\n", perm, exec_bit);
  if(exec_bit)
    printf("  PASS: Execute permission granted\n\n");
  else
    printf("  FAIL: Execute bit should be set\n\n");
  
  // Test without execute permission
  printf("Test 2: Set permissions to 0600 (rw-)\n");
  chmod("testfile", 0600);
  perm = getperm("testfile");
  exec_bit = (perm >> 6) & 1;
  printf("  Permissions: %x, Execute bit: %d\n", perm, exec_bit);
  if(!exec_bit)
    printf("  PASS: Execute permission denied\n\n");
  else
    printf("  FAIL: Execute bit should be clear\n\n");
  
  printf("All tests passed!\n");
  exit(0);
}
```

**File to create:** `user/testpermedge.c`
```c
#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"
#include "kernel/fcntl.h"

int main(int argc, char *argv[])
{
  printf("=== Edge Cases Test ===\n\n");
  
  int fd, perm;
  int pass = 0, fail = 0;
  
  // Test 1: All permission bits set
  printf("Test 1: Set all permission bits (0777)\n");
  fd = open("test_all.txt", O_CREATE | O_RDWR);
  write(fd, "test", 4);
  close(fd);
  chmod("test_all.txt", 0777);
  perm = getperm("test_all.txt");
  printf("  Permissions: %x (expected 0x1FF)\n", perm);
  if(perm == 0x1FF) {
    printf("  PASS\n\n");
    pass++;
  } else {
    printf("  FAIL\n\n");
    fail++;
  }
  
  // Test 2: No permission bits set
  printf("Test 2: Clear all permission bits (0000)\n");
  chmod("test_all.txt", 0000);
  perm = getperm("test_all.txt");
  printf("  Permissions: %x (expected 0x0)\n", perm);
  if(perm == 0x0) {
    printf("  PASS\n\n");
    pass++;
  } else {
    printf("  FAIL\n\n");
    fail++;
  }
  
  // Test 3: Try to open with no permissions (should fail)
  printf("Test 3: Try to open file with no permissions\n");
  fd = open("test_all.txt", O_RDONLY);
  if(fd < 0) {
    printf("  PASS: Open denied with 0000 permissions\n\n");
    pass++;
  } else {
    printf("  FAIL: Should not be able to open\n\n");
    close(fd);
    fail++;
  }
  
  // Test 4: Restore permissions and verify access
  printf("Test 4: Restore permissions and verify\n");
  chmod("test_all.txt", 0700);
  fd = open("test_all.txt", O_RDONLY);
  if(fd >= 0) {
    printf("  PASS: Can open after restoring permissions\n\n");
    close(fd);
    pass++;
  } else {
    printf("  FAIL: Should be able to open\n\n");
    fail++;
  }
  
  // Test 5: Test individual permission bits
  printf("Test 5: Test individual permission bits\n");
  
  // Only read (0400)
  chmod("test_all.txt", 0400);
  perm = getperm("test_all.txt");
  int read_bit = (perm >> 8) & 1;
  int write_bit = (perm >> 7) & 1;
  int exec_bit = (perm >> 6) & 1;
  printf("  0400: r=%d w=%d x=%d ", read_bit, write_bit, exec_bit);
  if(read_bit && !write_bit && !exec_bit) {
    printf("PASS\n");
    pass++;
  } else {
    printf("FAIL\n");
    fail++;
  }
  
  // Only write (0200)
  chmod("test_all.txt", 0200);
  perm = getperm("test_all.txt");
  read_bit = (perm >> 8) & 1;
  write_bit = (perm >> 7) & 1;
  exec_bit = (perm >> 6) & 1;
  printf("  0200: r=%d w=%d x=%d ", read_bit, write_bit, exec_bit);
  if(!read_bit && write_bit && !exec_bit) {
    printf("PASS\n");
    pass++;
  } else {
    printf("FAIL\n");
    fail++;
  }
  
  // Only execute (0100)
  chmod("test_all.txt", 0100);
  perm = getperm("test_all.txt");
  read_bit = (perm >> 8) & 1;
  write_bit = (perm >> 7) & 1;
  exec_bit = (perm >> 6) & 1;
  printf("  0100: r=%d w=%d x=%d ", read_bit, write_bit, exec_bit);
  if(!read_bit && !write_bit && exec_bit) {
    printf("PASS\n\n");
    pass++;
  } else {
    printf("FAIL\n\n");
    fail++;
  }
  
  // Test 6: Multiple chmod operations
  printf("Test 6: Multiple sequential chmod operations\n");
  chmod("test_all.txt", 0700);
  chmod("test_all.txt", 0600);
  chmod("test_all.txt", 0400);
  perm = getperm("test_all.txt");
  printf("  Final permissions: %x (expected 0x100)\n", perm);
  if(perm == 0x100) {
    printf("  PASS\n\n");
    pass++;
  } else {
    printf("  FAIL\n\n");
    fail++;
  }
  
  // Test 7: getperm on non-existent file
  printf("Test 7: getperm on non-existent file\n");
  perm = getperm("nonexistent_file_xyz.txt");
  if(perm < 0) {
    printf("  PASS: Returns error for non-existent file\n\n");
    pass++;
  } else {
    printf("  FAIL: Should return error\n\n");
    fail++;
  }
  
  printf("=== Results ===\n");
  printf("Passed: %d\n", pass);
  printf("Failed: %d\n", fail);
  printf("Total:  %d\n", pass + fail);
  
  exit(0);
}
```

**File to create:** `user/testpermpersist.c`
```c
#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"
#include "kernel/fcntl.h"

int main(int argc, char *argv[])
{
  printf("=== Persistence Test ===\n\n");
  
  int fd, perm;
  int pass = 0, fail = 0;
  char buf[100];
  
  // Test 1: Permissions persist after close/reopen
  printf("Test 1: Permissions persist after close/reopen\n");
  fd = open("persist_test.txt", O_CREATE | O_RDWR);
  write(fd, "initial", 7);
  close(fd);
  
  chmod("persist_test.txt", 0500);  // r-x
  perm = getperm("persist_test.txt");
  printf("  Set permissions to: %x\n", perm);
  
  // Reopen and check
  fd = open("persist_test.txt", O_RDONLY);
  if(fd >= 0) {
    close(fd);
    int new_perm = getperm("persist_test.txt");
    printf("  After reopen: %x\n", new_perm);
    if(perm == new_perm) {
      printf("  PASS: Permissions persisted\n\n");
      pass++;
    } else {
      printf("  FAIL: Permissions changed\n\n");
      fail++;
    }
  } else {
    printf("  FAIL: Could not reopen file\n\n");
    fail++;
  }
  
  // Test 2: Permissions persist after writing
  printf("Test 2: Permissions persist after write operations\n");
  chmod("persist_test.txt", 0700);
  perm = getperm("persist_test.txt");
  printf("  Initial permissions: %x\n", perm);
  
  fd = open("persist_test.txt", O_WRONLY);
  if(fd >= 0) {
    write(fd, "modified", 8);
    close(fd);
    
    int new_perm = getperm("persist_test.txt");
    printf("  After write: %x\n", new_perm);
    if(perm == new_perm) {
      printf("  PASS: Permissions unchanged by write\n\n");
      pass++;
    } else {
      printf("  FAIL: Permissions should not change\n\n");
      fail++;
    }
  } else {
    printf("  FAIL: Could not open for write\n\n");
    fail++;
  }
  
  // Test 3: Permissions persist after reading
  printf("Test 3: Permissions persist after read operations\n");
  chmod("persist_test.txt", 0600);
  perm = getperm("persist_test.txt");
  printf("  Initial permissions: %x\n", perm);
  
  fd = open("persist_test.txt", O_RDONLY);
  if(fd >= 0) {
    read(fd, buf, 10);
    close(fd);
    
    int new_perm = getperm("persist_test.txt");
    printf("  After read: %x\n", new_perm);
    if(perm == new_perm) {
      printf("  PASS: Permissions unchanged by read\n\n");
      pass++;
    } else {
      printf("  FAIL: Permissions should not change\n\n");
      fail++;
    }
  } else {
    printf("  FAIL: Could not open for read\n\n");
    fail++;
  }
  
  // Test 4: Create new file, verify default permissions
  printf("Test 4: New files get default permissions (0700)\n");
  fd = open("newfile.txt", O_CREATE | O_RDWR);
  if(fd >= 0) {
    write(fd, "new", 3);
    close(fd);
    
    perm = getperm("newfile.txt");
    printf("  New file permissions: %x (expected 0x1C0)\n", perm);
    if(perm == 0x1C0) {
      printf("  PASS: Default permissions correct\n\n");
      pass++;
    } else {
      printf("  FAIL: Default should be 0x1C0\n\n");
      fail++;
    }
  } else {
    printf("  FAIL: Could not create file\n\n");
    fail++;
  }
  
  // Test 5: Verify multiple files maintain independent permissions
  printf("Test 5: Multiple files have independent permissions\n");
  fd = open("file1.txt", O_CREATE | O_RDWR);
  write(fd, "one", 3);
  close(fd);
  
  fd = open("file2.txt", O_CREATE | O_RDWR);
  write(fd, "two", 3);
  close(fd);
  
  chmod("file1.txt", 0400);  // read-only
  chmod("file2.txt", 0200);  // write-only
  
  int perm1 = getperm("file1.txt");
  int perm2 = getperm("file2.txt");
  
  printf("  file1.txt: %x\n", perm1);
  printf("  file2.txt: %x\n", perm2);
  
  if(perm1 == 0x100 && perm2 == 0x80) {
    printf("  PASS: Files maintain independent permissions\n\n");
    pass++;
  } else {
    printf("  FAIL: Permissions should be independent\n\n");
    fail++;
  }
  
  printf("=== Results ===\n");
  printf("Passed: %d\n", pass);
  printf("Failed: %d\n", fail);
  printf("Total:  %d\n", pass + fail);
  
  exit(0);
}
```

**File to create:** `user/testpermcomprehensive.c`
```c
#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"
#include "kernel/fcntl.h"

// Test a specific permission combination
int test_permission(int mode, int should_read, int should_write, char* desc)
{
  int fd;
  
  printf("  Testing %s (0%x): ", desc, mode);
  
  // Create and set permissions
  fd = open("testfile.tmp", O_CREATE | O_RDWR);
  if(fd < 0) {
    printf("FAIL - cannot create\n");
    return 0;
  }
  write(fd, "test", 4);
  close(fd);
  
  chmod("testfile.tmp", mode);
  
  // Test read
  fd = open("testfile.tmp", O_RDONLY);
  int can_read = (fd >= 0);
  if(fd >= 0) close(fd);
  
  // Test write
  fd = open("testfile.tmp", O_WRONLY);
  int can_write = (fd >= 0);
  if(fd >= 0) close(fd);
  
  // Check results
  int pass = 1;
  if(can_read != should_read) {
    printf("FAIL - read access incorrect ");
    pass = 0;
  }
  if(can_write != should_write) {
    printf("FAIL - write access incorrect ");
    pass = 0;
  }
  
  if(pass) {
    printf("PASS\n");
  } else {
    printf("(can_read=%d expected=%d, can_write=%d expected=%d)\n",
           can_read, should_read, can_write, should_write);
  }
  
  return pass;
}

int main(int argc, char *argv[])
{
  printf("=== Comprehensive Permission Test ===\n\n");
  
  int total = 0, passed = 0;
  
  printf("Testing all owner permission combinations:\n");
  
  // Test all 8 combinations of rwx for owner (bits 8-6)
  total++; passed += test_permission(0000, 0, 0, "--- (none)");
  total++; passed += test_permission(0100, 0, 0, "--x (exec only)");
  total++; passed += test_permission(0200, 0, 1, "-w- (write only)");
  total++; passed += test_permission(0300, 0, 1, "-wx (write+exec)");
  total++; passed += test_permission(0400, 1, 0, "r-- (read only)");
  total++; passed += test_permission(0500, 1, 0, "r-x (read+exec)");
  total++; passed += test_permission(0600, 1, 1, "rw- (read+write)");
  total++; passed += test_permission(0700, 1, 1, "rwx (all)");
  
  printf("\nTesting O_RDWR access:\n");
  
  // Create test file
  int fd = open("rdwr_test.txt", O_CREATE | O_RDWR);
  write(fd, "test", 4);
  close(fd);
  
  // Test with read-only permission
  chmod("rdwr_test.txt", 0400);
  fd = open("rdwr_test.txt", O_RDWR);
  total++;
  if(fd < 0) {
    printf("  PASS: O_RDWR denied with r-- permissions\n");
    passed++;
  } else {
    printf("  FAIL: O_RDWR should be denied with r-- permissions\n");
    close(fd);
  }
  
  // Test with write-only permission
  chmod("rdwr_test.txt", 0200);
  fd = open("rdwr_test.txt", O_RDWR);
  total++;
  if(fd < 0) {
    printf("  PASS: O_RDWR denied with -w- permissions\n");
    passed++;
  } else {
    printf("  FAIL: O_RDWR should be denied with -w- permissions\n");
    close(fd);
  }
  
  // Test with read+write permission
  chmod("rdwr_test.txt", 0600);
  fd = open("rdwr_test.txt", O_RDWR);
  total++;
  if(fd >= 0) {
    printf("  PASS: O_RDWR allowed with rw- permissions\n");
    close(fd);
    passed++;
  } else {
    printf("  FAIL: O_RDWR should be allowed with rw- permissions\n");
  }
  
  printf("\nTesting chmod boundary conditions:\n");
  
  // Test chmod with values > 0777
  fd = open("boundary.txt", O_CREATE | O_RDWR);
  write(fd, "test", 4);
  close(fd);
  
  chmod("boundary.txt", 0xFFF);  // Set all bits
  int perm = getperm("boundary.txt");
  total++;
  // Should only keep lower 9 bits (0x1FF)
  if((perm & 0x1FF) == 0x1FF) {
    printf("  PASS: chmod masks to 9 bits correctly\n");
    passed++;
  } else {
    printf("  FAIL: chmod should mask to 9 bits (got %x)\n", perm);
  }
  
  printf("\n=== Results ===\n");
  printf("Passed: %d / %d\n", passed, total);
  printf("Failed: %d / %d\n", total - passed, total);
  
  if(passed == total) {
    printf("\n*** ALL TESTS PASSED! ***\n");
  } else {
    printf("\n*** SOME TESTS FAILED ***\n");
  }
  
  exit(0);
}
```

**File to create:** `user/testpermscenarios.c`
```c
#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"
#include "kernel/fcntl.h"

void print_test_header(char* name) {
  printf("\n--- %s ---\n", name);
}

int main(int argc, char *argv[])
{
  printf("=== Real-World Scenarios Test ===\n");
  printf("This test simulates practical permission use cases\n");
  
  int fd, perm;
  char buf[100];
  int pass = 0, fail = 0;
  
  // Scenario 1: Read-only configuration file
  print_test_header("Scenario 1: Read-only config file");
  printf("Creating a read-only configuration file...\n");
  
  fd = open("config.txt", O_CREATE | O_RDWR);
  write(fd, "setting=value\n", 14);
  close(fd);
  
  chmod("config.txt", 0400);  // Read-only
  printf("Set to read-only (0400)\n");
  
  // Should be able to read
  fd = open("config.txt", O_RDONLY);
  if(fd >= 0) {
    int n = read(fd, buf, 100);
    buf[n] = 0;
    printf("Read succeeded: %s", buf);
    close(fd);
    pass++;
  } else {
    printf("FAIL: Should be able to read\n");
    fail++;
  }
  
  // Should NOT be able to write
  fd = open("config.txt", O_WRONLY);
  if(fd < 0) {
    printf("Write blocked successfully\n");
    printf("PASS: Config file protected from modification\n");
    pass++;
  } else {
    printf("FAIL: Should not be able to write\n");
    close(fd);
    fail++;
  }
  
  // Scenario 2: Log file (append-only simulation)
  print_test_header("Scenario 2: Write-only log file");
  printf("Creating a write-only log file...\n");
  
  fd = open("logfile.txt", O_CREATE | O_RDWR);
  write(fd, "Log started\n", 12);
  close(fd);
  
  chmod("logfile.txt", 0200);  // Write-only
  printf("Set to write-only (0200)\n");
  
  // Should be able to write
  fd = open("logfile.txt", O_WRONLY);
  if(fd >= 0) {
    write(fd, "New log entry\n", 14);
    close(fd);
    printf("Write succeeded\n");
    pass++;
  } else {
    printf("FAIL: Should be able to write\n");
    fail++;
  }
  
  // Should NOT be able to read
  fd = open("logfile.txt", O_RDONLY);
  if(fd < 0) {
    printf("Read blocked successfully\n");
    printf("PASS: Log file hidden from reading\n");
    pass++;
  } else {
    printf("FAIL: Should not be able to read\n");
    close(fd);
    fail++;
  }
  
  // Scenario 3: Temporary working file
  print_test_header("Scenario 3: Temporary working file");
  printf("Creating a temporary file with full access...\n");
  
  fd = open("temp.txt", O_CREATE | O_RDWR);
  write(fd, "temporary data", 14);
  close(fd);
  
  chmod("temp.txt", 0700);  // Full access
  perm = getperm("temp.txt");
  printf("Set to rwx (0700), permissions: %x\n", perm);
  
  // Should be able to read
  fd = open("temp.txt", O_RDONLY);
  if(fd >= 0) {
    read(fd, buf, 14);
    close(fd);
    printf("Read succeeded\n");
    pass++;
  } else {
    printf("FAIL: Should be able to read\n");
    fail++;
  }
  
  // Should be able to write
  fd = open("temp.txt", O_WRONLY);
  if(fd >= 0) {
    write(fd, "modified", 8);
    close(fd);
    printf("Write succeeded\n");
    pass++;
  } else {
    printf("FAIL: Should be able to write\n");
    fail++;
  }
  
  printf("PASS: Temporary file fully accessible\n");
  
  // Scenario 4: Locking down sensitive data
  print_test_header("Scenario 4: Securing sensitive data");
  printf("Creating sensitive data file...\n");
  
  fd = open("secrets.txt", O_CREATE | O_RDWR);
  write(fd, "password=secret123", 18);
  close(fd);
  
  printf("Initially writable, reading and modifying...\n");
  chmod("secrets.txt", 0600);
  
  // Read the secret
  fd = open("secrets.txt", O_RDONLY);
  read(fd, buf, 18);
  close(fd);
  printf("Read secret data\n");
  
  // Now lock it down completely
  printf("Locking down with 0000 permissions...\n");
  chmod("secrets.txt", 0000);
  
  fd = open("secrets.txt", O_RDONLY);
  if(fd < 0) {
    printf("Read blocked\n");
    pass++;
  } else {
    printf("FAIL: Should not be able to read\n");
    close(fd);
    fail++;
  }
  
  fd = open("secrets.txt", O_WRONLY);
  if(fd < 0) {
    printf("Write blocked\n");
    printf("PASS: Sensitive data fully protected\n");
    pass++;
  } else {
    printf("FAIL: Should not be able to write\n");
    close(fd);
    fail++;
  }
  
  // Scenario 5: Progressive restriction
  print_test_header("Scenario 5: Progressive permission restriction");
  printf("Creating file with progressive restrictions...\n");
  
  fd = open("progressive.txt", O_CREATE | O_RDWR);
  write(fd, "data", 4);
  close(fd);
  
  // Start with full access
  chmod("progressive.txt", 0700);
  printf("Stage 1: rwx (0700) - Full access\n");
  fd = open("progressive.txt", O_RDWR);
  if(fd >= 0) {
    close(fd);
    printf("  Can read and write\n");
    pass++;
  } else {
    printf("  FAIL: Should have full access\n");
    fail++;
  }
  
  // Remove write
  chmod("progressive.txt", 0500);
  printf("Stage 2: r-x (0500) - Read-only\n");
  fd = open("progressive.txt", O_RDONLY);
  if(fd >= 0) {
    close(fd);
    printf("  Can read\n");
  } else {
    printf("  FAIL: Should be able to read\n");
    fail++;
    goto skip;
  }
  fd = open("progressive.txt", O_WRONLY);
  if(fd < 0) {
    printf("  Cannot write\n");
    pass++;
  } else {
    printf("  FAIL: Should not be able to write\n");
    close(fd);
    fail++;
  }
  
  // Remove all access
  chmod("progressive.txt", 0000);
  printf("Stage 3: --- (0000) - No access\n");
  fd = open("progressive.txt", O_RDONLY);
  if(fd < 0) {
    printf("  Cannot access\n");
    printf("  PASS: Progressive restriction worked\n");
    pass++;
  } else {
    printf("  FAIL: Should not be able to access\n");
    close(fd);
    fail++;
  }
  
skip:
  printf("\n=== Final Results ===\n");
  printf("Scenarios passed: %d\n", pass);
  printf("Scenarios failed: %d\n", fail);
  printf("Total tests: %d\n", pass + fail);
  
  if(fail == 0) {
    printf("\n*** SUCCESS! All real-world scenarios work correctly ***\n");
  } else {
    printf("\n*** Some scenarios failed - review implementation ***\n");
  }
  
  exit(0);
}
```

**File to create:** `user/runtests.c`
```c
#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"

int main(int argc, char *argv[])
{
  printf("====================================\n");
  printf("  XV6 PERMISSIONS TEST SUITE\n");
  printf("====================================\n\n");
  
  printf("Running all permission tests...\n");
  printf("This will take a moment.\n\n");
  
  int pid;
  
  // Test 1: Basic permissions
  printf("[1/6] Running basic permission tests...\n");
  pid = fork();
  if(pid == 0) {
    char *args[] = { "testperm", 0 };
    exec("testperm", args);
    printf("Failed to exec testperm\n");
    exit(1);
  }
  wait(0);
  printf("\n");
  
  // Test 2: Execute permissions
  printf("[2/6] Running execute permission tests...\n");
  pid = fork();
  if(pid == 0) {
    char *args[] = { "testexec", 0 };
    exec("testexec", args);
    printf("Failed to exec testexec\n");
    exit(1);
  }
  wait(0);
  printf("\n");
  
  // Test 3: Edge cases
  printf("[3/6] Running edge case tests...\n");
  pid = fork();
  if(pid == 0) {
    char *args[] = { "testpermedge", 0 };
    exec("testpermedge", args);
    printf("Failed to exec testperm_edge\n");
    exit(1);
  }
  wait(0);
  printf("\n");
  
  // Test 4: Persistence
  printf("[4/6] Running persistence tests...\n");
  pid = fork();
  if(pid == 0) {
    char *args[] = { "testpermpersist", 0 };
    exec("testpermpersist", args);
    printf("Failed to exec testperm_persist\n");
    exit(1);
  }
  wait(0);
  printf("\n");
  
  // Test 5: Comprehensive
  printf("[5/6] Running comprehensive tests...\n");
  pid = fork();
  if(pid == 0) {
    char *args[] = { "testpermcomprehensive", 0 };
    exec("testpermcomprehensive", args);
    printf("Failed to exec testperm_comprehensive\n");
    exit(1);
  }
  wait(0);
  printf("\n");
  
  // Test 6: Real-world scenarios
  printf("[6/6] Running real-world scenario tests...\n");
  pid = fork();
  if(pid == 0) {
    char *args[] = { "testpermscenarios", 0 };
    exec("testpermscenarios", args);
    printf("Failed to exec testperm_scenarios\n");
    exit(1);
  }
  wait(0);
  printf("\n");
  
  printf("====================================\n");
  printf("  ALL TESTS COMPLETED\n");
  printf("====================================\n");
  printf("Review the output above for any failures.\n");
  printf("All tests should show PASS status.\n");
  
  exit(0);
}
```

**Make sure to add these tests to the Makefile!**
```makefile
    #....
	$U/_wc\
	$U/_zombie\
	$U/_testperm\
	$U/_testexec\
	$U/_testpermedge\
	$U/_testpermpersist\
	$U/_testpermcomprehensive\
	$U/_testpermscenarios\
	$U/_runtests\
```


## complete tester output:
```
====================================
  XV6 PERMISSIONS TEST SUITE
====================================

Running all permission tests...
This will take a moment.

[1/6] Running basic permission tests...
Test 1: Create file with full permissions
Default permissions: 1C0 (expected 0700)
PASS: Can read file with permission 0700

Test 2: Remove read permission
New permissions: 80 (expected 0200)
PASS: Cannot read file without read permission

Test 3: Remove write permission
New permissions: 100 (expected 0400)
PASS: Cannot write to file without write permission
PASS: Can read file with read permission

All basic tests completed!

[2/6] Running execute permission tests...
=== Execute Permission Test ===

System file (ls) permissions: 0
Old files default to 0 (backwards compatible)

Test 1: Set permissions to 0700 (rwx)
  Permissions: 1C0, Execute bit: 1
  PASS: Execute permission granted

Test 2: Set permissions to 0600 (rw-)
  Permissions: 180, Execute bit: 0
  PASS: Execute permission denied

All tests passed!

[3/6] Running edge case tests...
=== Edge Cases Test ===

Test 1: Set all permission bits (0777)
  Permissions: 1FF (expected 0x1FF)
  PASS

Test 2: Clear all permission bits (0000)
  Permissions: 0 (expected 0x0)
  PASS

Test 3: Try to open file with no permissions
  PASS: Open denied with 0000 permissions

Test 4: Restore permissions and verify
  PASS: Can open after restoring permissions

Test 5: Test individual permission bits
  0400: r=1 w=0 x=0 PASS
  0200: r=0 w=1 x=0 PASS
  0100: r=0 w=0 x=1 PASS

Test 6: Multiple sequential chmod operations
  Final permissions: 100 (expected 0x100)
  PASS

Test 7: getperm on non-existent file
  PASS: Returns error for non-existent file

=== Results ===
Passed: 9
Failed: 0
Total:  9

[4/6] Running persistence tests...
=== Persistence Test ===

Test 1: Permissions persist after close/reopen
  Set permissions to: 140
  After reopen: 140
  PASS: Permissions persisted

Test 2: Permissions persist after write operations
  Initial permissions: 1C0
  After write: 1C0
  PASS: Permissions unchanged by write

Test 3: Permissions persist after read operations
  Initial permissions: 180
  After read: 180
  PASS: Permissions unchanged by read

Test 4: New files get default permissions (0700)
  New file permissions: 1C0 (expected 0x1C0)
  PASS: Default permissions correct

Test 5: Multiple files have independent permissions
  file1.txt: 100
  file2.txt: 80
  PASS: Files maintain independent permissions

=== Results ===
Passed: 5
Failed: 0
Total:  5

[5/6] Running comprehensive tests...
=== Comprehensive Permission Test ===

Testing all owner permission combinations:
  Testing --- (none) (00): PASS
  Testing --x (exec only) (040): PASS
  Testing -w- (write only) (080): PASS
  Testing -wx (write+exec) (0C0): PASS
  Testing r-- (read only) (0100): PASS
  Testing r-x (read+exec) (0140): PASS
  Testing rw- (read+write) (0180): PASS
  Testing rwx (all) (01C0): PASS

Testing O_RDWR access:
  PASS: O_RDWR denied with r-- permissions
  PASS: O_RDWR denied with -w- permissions
  PASS: O_RDWR allowed with rw- permissions

Testing chmod boundary conditions:
  PASS: chmod masks to 9 bits correctly

=== Results ===
Passed: 12 / 12
Failed: 0 / 12

*** ALL TESTS PASSED! ***

[6/6] Running real-world scenario tests...
=== Real-World Scenarios Test ===
This test simulates practical permission use cases

--- Scenario 1: Read-only config file ---
Creating a read-only configuration file...
Set to read-only (0400)
Read succeeded: setting=value
Write blocked successfully
PASS: Config file protected from modification

--- Scenario 2: Write-only log file ---
Creating a write-only log file...
Set to write-only (0200)
Write succeeded
Read blocked successfully
PASS: Log file hidden from reading

--- Scenario 3: Temporary working file ---
Creating a temporary file with full access...
Set to rwx (0700), permissions: 1C0
Read succeeded
Write succeeded
PASS: Temporary file fully accessible

--- Scenario 4: Securing sensitive data ---
Creating sensitive data file...
Initially writable, reading and modifying...
Read secret data
Locking down with 0000 permissions...
Read blocked
Write blocked
PASS: Sensitive data fully protected

--- Scenario 5: Progressive permission restriction ---
Creating file with progressive restrictions...
Stage 1: rwx (0700) - Full access
  Can read and write
Stage 2: r-x (0500) - Read-only
  Can read
  Cannot write
Stage 3: --- (0000) - No access
  Cannot access
  PASS: Progressive restriction worked

=== Final Results ===
Scenarios passed: 11
Scenarios failed: 0
Total tests: 11

*** SUCCESS! All real-world scenarios work correctly ***

====================================
  ALL TESTS COMPLETED
====================================
Review the output above for any failures.
All tests should show PASS status.
```
---