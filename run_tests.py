import os
import subprocess
import sys
import time
from datetime import datetime
PYTHON_EXE = sys.executable
# Параметры экспериментов
MATRIX_SIZES = [200, 400, 600, 800, 1200, 1600, 2000]
PROCESS_COUNTS = [1, 2, 4, 8]  # Количество MPI-процессов

# Файлы
MPI_SOURCE = "ConsoleApplication1.cpp"
MPI_EXE = "ConsoleApplication1.exe"
GENERATOR = "matrix_generation.py"
RESULT_STATS = "result_stats_mpi.txt"
VISUALIZER = "visualize_stats.py"

# Пути к MPI (для vcpkg)
MPI_INCLUDE = "C:/vcpkg/installed/x64-windows/include"
MPI_LIB = "C:/vcpkg/installed/x64-windows/lib"
MPI_EXEC = r"C:\Program Files\Microsoft MPI\Bin\mpiexec.exe"

def compile_mpi():
    """Компиляция MPI-программы с очисткой старых файлов"""
    print(f"🔨 Компиляция {MPI_SOURCE}...")
    
    # === ДОБАВЬ ЭТОТ БЛОК ===
    # Удаляем старые файлы, которые могут блокировать компиляцию
    old_files = [MPI_EXE, "ConsoleApplication1.exe", "*.obj", "*.pdb"]
    for pattern in old_files:
        try:
            import glob
            for f in glob.glob(pattern):
                os.remove(f)
                print(f"🗑️  Удалён старый файл: {f}")
        except PermissionError:
            print(f"⚠️  Не удалось удалить {pattern} — файл заблокирован")
            print("💡 Закрой все процессы и попробуй снова")
            return False
        except:
            pass
    # ========================
    
    MPI_INC_PATH = r"C:\Program Files (x86)\Microsoft SDKs\MPI\Include"
    MPI_LIB_PATH = r"C:\Program Files (x86)\Microsoft SDKs\MPI\Lib\x64"
    
    cmd = (f'cl.exe /O2 /EHsc /nologo '
           f'/I"{MPI_INC_PATH}" '
           f'{MPI_SOURCE} '
           f'/link /LIBPATH:"{MPI_LIB_PATH}" msmpi.lib '
           f'/Fe:{MPI_EXE}')
    
    print(f"   Команда: {cmd}")
    
    result = subprocess.run(
        cmd, 
        shell=True, 
        capture_output=True, 
        text=True, 
        encoding='cp866', 
        errors='replace'
    )
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    if result.returncode != 0:
        print("❌ Ошибка компиляции")
        return False
    
    if not os.path.exists(MPI_EXE):
        print(f"❌ Файл {MPI_EXE} не создан")
        return False
    
    print(f"✅ Успешно создан {MPI_EXE}")
    return True

def clear_stats():
    """Очистка старого файла статистики"""
    if os.path.exists(RESULT_STATS):
        os.remove(RESULT_STATS)
        print(f"🗑️  Удалён старый файл {RESULT_STATS}")

def generate_matrices(size):
    """Генерация матриц заданного размера"""
    cmd = f'"{sys.executable}" {GENERATOR} {size} --output_a matrix_A.txt --output_b matrix_B.txt'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Ошибка генерации матриц {size}×{size}:")
        print(result.stderr)
        return False
    
    return True

def run_experiment(size, num_procs):
    """Запуск одного эксперимента"""
    # Генерируем матрицы
    if not generate_matrices(size):
        return False
    
    # Формируем команду запуска
    if num_procs == 1:
        # Для 1 процесса можно без mpiexec
        cmd = f"{MPI_EXE}"
    else:
        cmd = f'"{MPI_EXEC}" -np {num_procs} {MPI_EXE}'
    
    # Замеряем время
    start_time = time.time()
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='cp866', errors='replace')
    elapsed = time.time() - start_time
    
    if result.returncode != 0:
        print(f"❌ Ошибка выполнения (size={size}, procs={num_procs}):")
        print(result.stderr)
        return False
    
    print(f"  ✓ N={size:4d}, procs={num_procs:2d} → {elapsed:.3f}s", end="")
    
    # Парсим GFLOPS из вывода, если есть
    for line in result.stdout.split('\n'):
        if 'GFLOPS:' in line:
            gflops = line.split('GFLOPS:')[-1].strip()
            print(f" | {gflops} GFLOPS", end="")
            break
    
    print()
    return True

def run_visualization():
    """Запуск визуализации результатов"""
    if not os.path.exists(RESULT_STATS):
        print(f"⚠️  Файл {RESULT_STATS} не найден. Пропускаем визуализацию.")
        return
    
    print(f"\n📊 Запуск визуализации...")
    cmd = f"python {VISUALIZER} {RESULT_STATS} results_plot.png"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❌ Ошибка визуализации:")
        print(result.stderr)
    else:
        print("✅ Визуализация завершена: results_plot.png")

def main():
    print("=" * 70)
    print("🔬 Автоматизация экспериментов: Умножение матриц на MPI")
    print("=" * 70)
    print(f"📊 Размеры матриц: {MATRIX_SIZES}")
    print(f"🔢 Количество процессов: {PROCESS_COUNTS}")
    print(f"📈 Всего экспериментов: {len(MATRIX_SIZES) * len(PROCESS_COUNTS)}")
    print("=" * 70 + "\n")
    
    # Компиляция
    if not compile_mpi():
        print("❌ Не удалось скомпилировать программу")
        return
    
    # Очистка статистики
    clear_stats()
    
    # Запуск экспериментов
    total = len(MATRIX_SIZES) * len(PROCESS_COUNTS)
    current = 0
    failed = 0
    
    print("🚀 Запуск экспериментов:\n")
    
    for size in MATRIX_SIZES:
        print(f"📐 Матрица {size}×{size}:")
        
        for num_procs in PROCESS_COUNTS:
            current += 1
            print(f"  [{current}/{total}] ", end="", flush=True)
            
            if not run_experiment(size, num_procs):
                failed += 1
        
        print()  # Пустая строка между размерами
    
    # Итоги
    print("\n" + "=" * 70)
    print(f"✅ Завершено: {current - failed}/{current} экспериментов")
    if failed > 0:
        print(f"❌ Ошибок: {failed}")
    print("=" * 70 + "\n")
    
    # Визуализация
    run_visualization()
    
    print(f"\n💾 Результаты сохранены в: {RESULT_STATS}")
    print(f"📊 Для анализа: python {VISUALIZER} {RESULT_STATS} plot.png")

if __name__ == "__main__":
    main()