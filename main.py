

cuda_code = r'''// matrix_multiply_cuda.cu
// Параллельное умножение матриц на CUDA
// Компиляция: nvcc -o matrix_cuda matrix_multiply_cuda.cu

#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <cmath>
#include <iomanip>
#include <cuda_runtime.h>

using namespace std;

__global__ void multiplyKernel(const double* A, const double* B, double* C, int N) {
    int row = blockIdx.y * blockDim.y + threadIdx.y;
    int col = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (row < N && col < N) {
        double sum = 0.0;
        for (int k = 0; k < N; ++k) {
            sum += A[row * N + k] * B[k * N + col];
        }
        C[row * N + col] = sum;
    }
}

#define TILE_SIZE 16

__global__ void multiplyKernelOptimized(const double* A, const double* B, double* C, int N) {
    __shared__ double As[TILE_SIZE][TILE_SIZE];
    __shared__ double Bs[TILE_SIZE][TILE_SIZE];
    
    int bx = blockIdx.x, by = blockIdx.y;
    int tx = threadIdx.x, ty = threadIdx.y;
    int row = by * TILE_SIZE + ty;
    int col = bx * TILE_SIZE + tx;
    
    double sum = 0.0;
    

    int numTiles = (N + TILE_SIZE - 1) / TILE_SIZE;
    
    for (int t = 0; t < numTiles; ++t) {
        int aCol = t * TILE_SIZE + tx;
        if (row < N && aCol < N) {
            As[ty][tx] = A[row * N + aCol];
        } else {
            As[ty][tx] = 0.0;
        }
        
        int bRow = t * TILE_SIZE + ty;
        if (bRow < N && col < N) {
            Bs[ty][tx] = B[bRow * N + col];
        } else {
            Bs[ty][tx] = 0.0;
        }
        
        __syncthreads();
        
        for (int k = 0; k < TILE_SIZE; ++k) {
            sum += As[ty][k] * Bs[k][tx];
        }
        
        __syncthreads();
    }
    
    if (row < N && col < N) {
        C[row * N + col] = sum;
    }
}


#define CUDA_CHECK(call) \
    do { \
        cudaError_t err = call; \
        if (err != cudaSuccess) { \
            cerr << "CUDA error: " << cudaGetErrorString(err) \
                 << " at " << __FILE__ << ":" << __LINE__ << endl; \
            exit(EXIT_FAILURE); \
        } \
    } while(0)

bool readMatrix(const string& filename, vector<double>& matrix) {
    ifstream file(filename);
    if (!file.is_open()) { cerr << "Не удалось открыть " << filename << endl; return false; }
    double value;
    while (file >> value) matrix.push_back(value);
    file.close();
    if (matrix.empty()) { cerr << "Файл пустой" << endl; return false; }
    size_t count = matrix.size();
    int N = static_cast<int>(sqrt(count));
    if (N * N != static_cast<int>(count)) { cerr << "Ошибка: не квадрат" << endl; matrix.clear(); return false; }
    return true;
}

bool writeMatrix(const string& filename, const vector<double>& matrix, int N) {
    ofstream file(filename);
    if (!file.is_open()) return false;
    file << fixed << setprecision(6);
    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) file << matrix[i * N + j] << " ";
        file << endl;
    }
    return true;
}

bool writeStats(const string& filename, int N, int blockSize, double timeSec, long long flops) {
    ofstream file(filename, ios::app);
    if (!file.is_open()) return false;
    file << fixed << setprecision(6);
    file << "size: " << N << " | block: " << blockSize << endl;
    file << "time_sec: " << timeSec << endl;
    file << "flops: " << flops << endl;
    file << "-------------------" << endl;
    return true;
}

int main(int argc, char** argv) {
    string fileA = "matrix_A.txt", fileB = "matrix_B.txt";
    string fileResult = "result_matrix.txt", fileStats = "result_stats_cuda.txt";
    int blockSize = 16;
    
    for (int i = 1; i < argc; ++i) {
        string arg = argv[i];
        if (arg == "--block" && i + 1 < argc) blockSize = stoi(argv[++i]);
    }
    
    vector<double> A, B;
    if (!readMatrix(fileA, A) || !readMatrix(fileB, B)) { cerr << "Ошибка чтения" << endl; return 1; }
    
    int N = static_cast<int>(sqrt(A.size()));
    cout << " Матрица: " << N << "×" << N << ", блок: " << blockSize << "×" << blockSize << endl;
    
    double *d_A, *d_B, *d_C;
    size_t bytes = N * N * sizeof(double);
    CUDA_CHECK(cudaMalloc(&d_A, bytes));
    CUDA_CHECK(cudaMalloc(&d_B, bytes));
    CUDA_CHECK(cudaMalloc(&d_C, bytes));
    
    CUDA_CHECK(cudaMemcpy(d_A, A.data(), bytes, cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(d_B, B.data(), bytes, cudaMemcpyHostToDevice));
    
    dim3 blockDim(blockSize, blockSize);
    dim3 gridDim((N + blockSize - 1) / blockSize, (N + blockSize - 1) / blockSize);
    
    cudaEvent_t start, stop;
    CUDA_CHECK(cudaEventCreate(&start));
    CUDA_CHECK(cudaEventCreate(&stop));
    CUDA_CHECK(cudaEventRecord(start));
    
    multiplyKernelOptimized<<<gridDim, blockDim>>>(d_A, d_B, d_C, N);
    
    CUDA_CHECK(cudaEventRecord(stop));
    CUDA_CHECK(cudaEventSynchronize(stop));
    
    float elapsedMs = 0;
    CUDA_CHECK(cudaEventElapsedTime(&elapsedMs, start, stop));
    double timeSec = elapsedMs / 1000.0;
    
    vector<double> C(N * N);
    CUDA_CHECK(cudaMemcpy(C.data(), d_C, bytes, cudaMemcpyDeviceToHost));
    
    CUDA_CHECK(cudaFree(d_A)); CUDA_CHECK(cudaFree(d_B)); CUDA_CHECK(cudaFree(d_C));
    CUDA_CHECK(cudaEventDestroy(start)); CUDA_CHECK(cudaEventDestroy(stop));
    
    if (!writeMatrix(fileResult, C, N)) return 1;
    
    long long flops = 2LL * N * N * N;
    if (!writeStats(fileStats, N, blockSize, timeSec, flops)) return 1;
    
    double gflops = flops / timeSec / 1e9;
    cout << "Done: " << N << "×" << N 
         << ", block: " << blockSize << "×" << blockSize
         << ", time: " << timeSec << "s"
         << ", GFLOPS: " << gflops << endl;
    
    return 0;
}
'''


with open("matrix_multiply_cuda.cu", "w") as f:
    f.write(cuda_code)
print("CUDA-код сохранён: matrix_multiply_cuda.cu")



import os
import subprocess
import time
import sys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict


MATRIX_SIZES = [200, 400, 600, 800, 1200]  # 1600+ могут не влезть в память Colab
BLOCK_SIZES = [8, 16]

CUDA_SOURCE = "matrix_multiply_cuda.cu"
CUDA_EXE = "./matrix_cuda"
RESULT_STATS = "result_stats_cuda.txt"

def check_gpu():
    print("Проверка GPU")
    result = subprocess.run("nvidia-smi --query-gpu=name --format=csv,noheader", 
                          shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        gpu_name = result.stdout.strip()
        print(f"GPU обнаружен: {gpu_name}")
        return True
    else:
        print("GPU не найден!")
        return False

def compile_cuda():
    print(f"\nКомпиляция {CUDA_SOURCE}...")
    
    for arch in ["sm_75", "sm_70", "sm_60"]:
        cmd = f"nvcc -o {CUDA_EXE} {CUDA_SOURCE} -O3 -arch={arch} 2>&1"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Компиляция успешна (arch={arch})")
            return True
        else:
            print(f"arch={arch} не подошёл, пробуем следующую...")
    
    print("Ошибка компиляции:")
    print(result.stderr)
    return False

def generate_matrices(size):
    np.random.seed(42)
    A = np.random.rand(size, size).astype(np.float64)
    B = np.random.rand(size, size).astype(np.float64)
    np.savetxt('matrix_A.txt', A, fmt='%.6f')
    np.savetxt('matrix_B.txt', B, fmt='%.6f')
    return True

def run_experiment(size, block_size):
    generate_matrices(size)
    
    cmd = f"{CUDA_EXE} --block {block_size}"
    start_time = time.time()
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    elapsed = time.time() - start_time
    
    if result.returncode != 0:
        print(f"Ошибка (N={size}, block={block_size}): {result.stderr[:100]}")
        return None
    

    gflops = None
    for line in result.stdout.split('\n'):
        if 'GFLOPS:' in line:
            try:
                gflops = float(line.split('GFLOPS:')[-1].strip())
            except:
                pass
            break
    
    print(f"  N={size:4d}, block={block_size:2d}×{block_size:2d} → {elapsed:.3f}s", end="")
    if gflops:
        print(f" | {gflops:.2f} GFLOPS", end="")
    print()
    
    return {
        'size': size,
        'block': block_size,
        'time': elapsed,
        'gflops': gflops
    }

def plot_results(results):
    if not results:
        print("Нет данных для визуализации")
        return
    
    by_block = defaultdict(list)
    for r in results:
        if r['gflops']:
            by_block[r['block']].append(r)
    
    plt.figure(figsize=(14, 6))
    
    plt.subplot(1, 2, 1)
    colors = plt.cm.viridis(np.linspace(0, 1, len(by_block)))
    for (block, data), color in zip(by_block.items(), colors):
        sizes = [r['size'] for r in data]
        gflops = [r['gflops'] for r in data]
        plt.plot(sizes, gflops, 'o-', label=f'Block {block}×{block}', color=color, markersize=4)
    
    plt.xlabel('Размер матрицы (N×N)')
    plt.ylabel('Производительность (GFLOPS)')
    plt.title('Производительность CUDA')
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=9)
    plt.xscale('log')
    

    plt.subplot(1, 2, 2)
    for (block, data), color in zip(by_block.items(), colors):
        sizes = [r['size'] for r in data]
        times = [r['time'] for r in data]
        plt.plot(sizes, times, 's--', label=f'Block {block}×{block}', color=color, markersize=4)
    
    plt.xlabel('Размер матрицы (N×N)')
    plt.ylabel('Время (секунды)')
    plt.title('Время выполнения')
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=9)
    plt.xscale('log')
    plt.yscale('log')
    
    plt.suptitle('Результаты экспериментов: умножение матриц на CUDA', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('results_plot_cuda.png', dpi=150, bbox_inches='tight')
    print("Графики сохранены: results_plot_cuda.png")
    
    plt.show()

def print_summary(results):
    if not results:
        return
    
    print("\n" + "=" * 70)
    print("СВОДКА РЕЗУЛЬТАТОВ")
    print("=" * 70)
    print(f"{'Size':<8} {'Block':<10} {'Time(s)':<12} {'GFLOPS':<12}")
    print("-" * 70)
    
    for r in sorted(results, key=lambda x: (x['size'], x['block'])):
        gf = f"{r['gflops']:.2f}" if r['gflops'] else "N/A"
        print(f"{r['size']:<8} {r['block']:2d}×{r['block']:<7} {r['time']:<12.4f} {gf:<12}")
    
    print("=" * 70)
    
    if any(r['gflops'] for r in results):
        best = max((r for r in results if r['gflops']), key=lambda x: x['gflops'])
        print(f"\nЛучшая производительность: {best['gflops']:.2f} GFLOPS")
        print(f"   Параметры: N={best['size']}, блок={best['block']}×{best['block']}")

def main():
    print("=" * 70)
    print("CUDA Matrix Multiplication — Автоматизация экспериментов")
    print("=" * 70)
    

    if not check_gpu():
        return
    

    if not compile_cuda():
        return
    

    if os.path.exists(RESULT_STATS):
        os.remove(RESULT_STATS)
    

    total = len(MATRIX_SIZES) * len(BLOCK_SIZES)
    current = 0
    results = []
    
    print(f"\nЗапуск {total} экспериментов:\n")
    
    for size in MATRIX_SIZES:
        print(f"Матрица {size}×{size}:")
        for block in BLOCK_SIZES:
            current += 1
            print(f"  [{current}/{total}] ", end="", flush=True)
            res = run_experiment(size, block)
            if res:
                results.append(res)
                flops = int(res['gflops'] * 1e9) if res['gflops'] else 2 * size**3
                with open(RESULT_STATS, 'a') as f:
                    f.write(f"size: {size} | block: {block}\n")
                    f.write(f"time_sec: {res['time']:.6f}\n")
                    f.write(f"flops: {flops}\n")
                    f.write("-------------------\n")
            else:
                print(" Пропущено")
        print()
    

    print_summary(results)
    

    print("\nПостроение графиков...")
    plot_results(results)
    
    print("\n Готово!")


if __name__ == "__main__":
    main()