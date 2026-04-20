#include <iostream>
#include <fstream>
#include <vector>
#include <chrono>
#include <iomanip>
#include <string>

#include <mpi.h>

using namespace std;

void multiplyMatrices(const vector<double>& A, const vector<double>& B,
    vector<double>& C, int localRows, int N) {
    for (int i = 0; i < localRows; ++i) {
        for (int k = 0; k < N; ++k) {
            double r = A[i * N + k];
            for (int j = 0; j < N; ++j) {
                C[i * N + j] += r * B[k * N + j];
            }
        }
    }
}

bool readMatrix(const string& filename, vector<double>& matrix) {
    ifstream file(filename);
    if (!file.is_open()) {
        cerr << "Не удалось открыть файл " << filename << endl;
        return false;
    }

    double value;
    while (file >> value) {
        matrix.push_back(value);
    }
    file.close();

    if (matrix.empty()) {
        cerr << "Файл пустой" << endl;
        return false;
    }

    size_t count = matrix.size();
    int N = static_cast<int>(sqrt(count));

    if (N * N != static_cast<int>(count)) {
        cerr << "Ошибка: Количество элементов не является квадратом целого числа" << endl;
        matrix.clear();
        return false;
    }

    return true;
}
bool writeMatrix(const string& filename, const vector<double>& matrix,int N) {
    ofstream file(filename);
    if (!file.is_open()) {
        cerr << "Не удалось создать файл " << filename << endl;
        return false;
    }


    file << fixed << setprecision(6);
    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) {
            file << matrix[i * N + j] << " ";
        }
        file << endl;
    }
    file.close();
    return true;
}

bool writeStats(const string& filename, int N, int procCount, double timeSec, long long flops) {
    ofstream file(filename, ios::app);
    if (!file.is_open()) {
        cerr << "Не удалось создать файл " << filename << endl;
        return false;
    }

    file << fixed << setprecision(6);
    file << "size: " << N << " | procs: " << procCount << endl;  // ← Добавили procs
    file << "time_sec: " << timeSec << endl;
    file << "flops: " << flops << endl;
    file << "-------------------" << endl;
    file.close();
    return true;
}

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);
    
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    
    string fileA = "matrix_A.txt";
    string fileB = "matrix_B.txt";
    string fileResult = "result_matrix.txt";  // ← ИСПРАВЛЕНО
    string fileStats = "result_stats_mpi.txt";  // ← ИСПРАВЛЕНО

    vector<double> A, B, C;
    int N = 0;

    // Чтение только на процессе 0
    if (rank == 0) {
        if (!readMatrix(fileA, A)) MPI_Abort(MPI_COMM_WORLD, 1);
        if (!readMatrix(fileB, B)) MPI_Abort(MPI_COMM_WORLD, 1);
        N = static_cast<int>(sqrt(A.size()));
        C.resize(N * N, 0.0);
        cout << "[Rank 0] Loaded matrices " << N << "x" << N << endl;
    }

    // Рассылка размера
    MPI_Bcast(&N, 1, MPI_INT, 0, MPI_COMM_WORLD);

    // ВСЕ процессы выделяют память под B (включая rank 0!)
    B.resize(N * N);

    // Рассылка матрицы B (ОДИН РАЗ!)
    MPI_Bcast(B.data(), N * N, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    // Расчёт распределения строк
    int baseRows = N / size;
    int extra = N % size;
    int localRows = baseRows + (rank < extra ? 1 : 0);
    
    vector<int> sendCounts(size), displs(size);
    int offset = 0;
    for (int p = 0; p < size; ++p) {
        int rows = baseRows + (p < extra ? 1 : 0);
        sendCounts[p] = rows * N;
        displs[p] = offset;
        offset += sendCounts[p];
    }

    // Локальные буферы
    vector<double> localA(localRows * N);
    vector<double> localC(localRows * N, 0.0);
    // localB больше не нужен — используем глобальный B

    // Рассылка частей A
    MPI_Scatterv(A.data(), sendCounts.data(), displs.data(), MPI_DOUBLE,
                 localA.data(), localRows * N, MPI_DOUBLE,
                 0, MPI_COMM_WORLD);

    // Замер времени и умножение (используем B напрямую!)
    double startTime = MPI_Wtime();
    multiplyMatrices(localA, B, localC, localRows, N);  // ← B вместо localB
    double endTime = MPI_Wtime();
    double localTime = endTime - startTime;

    // Сбор результата
    MPI_Gatherv(localC.data(), localRows * N, MPI_DOUBLE,
                C.data(), sendCounts.data(), displs.data(), MPI_DOUBLE,
                0, MPI_COMM_WORLD);

    // Сохранение (только rank 0)
    if (rank == 0) {
        if (!writeMatrix(fileResult, C, N)) return 1;
        
        double maxTime;
        MPI_Reduce(&localTime, &maxTime, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
        
        long long flops = 2LL * N * N * N;
        if (!writeStats(fileStats, N, size, maxTime, flops)) return 1;
        
        cout << "Done: " << N << "x" << N << ", procs: " << size 
             << ", time: " << maxTime << "s"
             << ", GFLOPS: " << flops / maxTime / 1e9 << endl;
    } else {
        double dummy;
        MPI_Reduce(&localTime, &dummy, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    }

    MPI_Finalize();
    return 0;
}