import subprocess
import json
import os
import shutil
import signal
import stat
import sys

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException

def compile_c_files():
    # Compiling without sudo is usually better, but keeping your logic
    subprocess.run(["gcc", "part3.c", "copytree.c", "-o", "copytree"], check=True)

def on_rm_error(func, path, exc_info):
    # Attempt to fix permissions and retry deletion
    try:
        if not os.path.islink(path):
            os.chmod(path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
        func(path)
    except Exception:
        pass

def setup_test_environment(test_case):
    # Ensure clean start for this case
    if os.path.exists(test_case['source_directory']):
        shutil.rmtree(test_case['source_directory'], onerror=on_rm_error)
        
    os.makedirs(test_case['source_directory'], exist_ok=True)
    
    for item in test_case['items']:
        item_path = os.path.join(test_case['source_directory'], item['name'])
        
        if item['type'] == 'directory':
            os.makedirs(item_path, exist_ok=True)
            
        elif item['type'] == 'file':
            os.makedirs(os.path.dirname(item_path), exist_ok=True)
            with open(item_path, 'w') as f:
                f.write(item['content'])
            
        elif item['type'] == 'symlink':
            os.makedirs(os.path.dirname(item_path), exist_ok=True)
            if os.path.lexists(item_path):
                os.unlink(item_path)
            os.symlink(item['target'], item_path)

    # Sort items by length (descending) to apply permissions to children before parents
    sorted_items = sorted(test_case['items'], key=lambda x: len(x['name']), reverse=True)
    
    for item in sorted_items:
        if 'permissions' in item:
            item_path = os.path.join(test_case['source_directory'], item['name'])
            # Only apply chmod if it exists and is NOT a symlink
            if os.path.exists(item_path) and not os.path.islink(item_path):
                try:
                    os.chmod(item_path, item['permissions'])
                except OSError:
                    pass

def run_test_case(test_case):
    setup_test_environment(test_case)
    
    # Ensure destination is clean
    if os.path.exists(test_case['destination_directory']):
        shutil.rmtree(test_case['destination_directory'], onerror=on_rm_error)

    command = ["./copytree"]
    if test_case['copy_symlinks']:
        command.append("-l")
    if test_case['copy_permissions']:
        command.append("-p")
    command.extend([test_case['source_directory'], test_case['destination_directory']])
    
    # Running C program
    subprocess.run(command, check=True)

def verify_test_result(test_case):
    for item in test_case['items']:
        dest_item_path = os.path.join(test_case['destination_directory'], item['name'])
        if item['type'] == 'file':
            if not os.path.isfile(dest_item_path):
                return False
            if (os.stat(dest_item_path).st_mode & 0o777) != (item['permissions'] & 0o777) and test_case['copy_permissions']:
                return False
        elif item['type'] == 'directory':
            if not os.path.isdir(dest_item_path):
                return False
            if (os.stat(dest_item_path).st_mode & 0o777) != (item['permissions'] & 0o777) and test_case['copy_permissions']:
                return False
        elif item['type'] == 'symlink':
            if test_case['copy_symlinks']:
                if not os.path.islink(dest_item_path):
                    return False
                if os.readlink(dest_item_path) != item['target']:
                    return False
    return True

def run_tests():
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(30)

    try:
        with open('test_cases.json', 'r') as f:
            test_cases = json.load(f)

        compile_c_files()

        results = []
        for i, test_case in enumerate(test_cases, 1):
            # Cleanup before test
            if os.path.exists(test_case['source_directory']):
                shutil.rmtree(test_case['source_directory'], onerror=on_rm_error)
            if os.path.exists(test_case['destination_directory']):
                shutil.rmtree(test_case['destination_directory'], onerror=on_rm_error)

            try:
                run_test_case(test_case)
                status = "PASSED" if verify_test_result(test_case) else "FAILED"
            except Exception as e:
                print(f"Test {i} crashed: {e}")
                status = "FAILED"

            result = {
                "test_name": test_case['description'],
                "test_number": i,
                "status": status
            }
            results.append(result)

        signal.alarm(0)

        with open('test_output.txt', 'w') as f:
            for result in results:
                f.write(f"TEST_{result['test_number']}, {result['status']}\n")

        return json.dumps(results, indent=4)

    except TimeoutException:
        results = []
        # In case of timeout, we might not have 'test_cases' loaded if it failed early, 
        # but usually it fails during run. Assuming test_cases loaded.
        if 'test_cases' in locals():
            for i, test_case in enumerate(test_cases, 1):
                results.append({
                    "test_name": test_case['description'],
                    "test_number": i,
                    "status": "FAILED"
                })

        with open('test_output.txt', 'w') as f:
            for result in results:
                f.write(f"TEST_{result['test_number']}, {result['status']}\n")

        return json.dumps(results, indent=4)

def main():
    if os.geteuid() != 0:
        print("Error: You must run this script with sudo.")
        print("Try: sudo python3 part3_tests.py")
        sys.exit(1)
    
    print(run_tests())

if __name__ == "__main__":
    main()