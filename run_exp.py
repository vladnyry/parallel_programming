import os
import subprocess
MATRIX_SIZES = [200, 400, 600, 800, 1200, 1600, 2000]
THREAD_COUNTS = [1, 2, 4, 8, 12]

source_file_cpp = "ConsoleApplication1.cpp"
exe_cpp = "ConsoleApplication1.exe"
generator = "matrix_generation.py"
res_stat = "results_stat.txt"
visualizer = "visualize_stats.py"

def compile_OPENMP():
    print(f"Компилияция {source_file_cpp}")
    cmd = f"cl /O2 /openmp {source_file_cpp}"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='cp866', errors='replace')
    if res.returncode != 0:
        print("Ошибка компиляции")
        print(res.stderr) 
        return False
    return True

def clear_stats():
    if os.path.exists(res_stat):
        os.remove(res_stat)
        
def run_experiments(size, num_threads):
    generator_cmd = f"python {generator} {size}"
    subprocess.run(generator_cmd, shell=True, capture_output=True)
    
    run_cmd = f"{exe_cpp} matrix_A.txt matrix_B.txt result_matrix.txt {res_stat} {num_threads}"
    result = subprocess.run(run_cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        return True
    else:
        return False
    
def run_visualization():
    cmd = f"python {visualizer} {res_stat}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

def main():
    if not compile_OPENMP():
        return
    
    clear_stats()
    
    for size in MATRIX_SIZES:
        for num_threads in THREAD_COUNTS:
            if not run_experiments(size, num_threads):
                print(f"эксперимент пошел не по плану")
                return
    run_visualization()
if __name__ == "__main__":
    main()