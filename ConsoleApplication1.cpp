#include <iostream>
#include <fstream>
#include <vector>
#include <chrono>
#include <iomanip>
#include <string>

using namespace std;

void multiplyMatrices(const vector<double>& A, const vector<double>& B,
    vector<double>& C) {
    int N = static_cast<int>(sqrt(A.size()));

    for (int i = 0; i < N; ++i) {
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
bool writeMatrix(const string& filename, const vector<double>& matrix) {
    ofstream file(filename);
    if (!file.is_open()) {
        cerr << "Не удалось создать файл " << filename << endl;
        return false;
    }

    int N = static_cast<int>(sqrt(matrix.size()));

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

bool writeStats(const string& filename, int N, double timeSec, long long flops) {
    ofstream file(filename, ios::app);
    if (!file.is_open()) {
        cerr << "Не удалось создать файл " << filename << endl;
        return false;
    }

    file << fixed << setprecision(6);
    file << "size: " << N << endl;
    file << "time_sec: " << timeSec << endl;
    file << "flops: " << flops << endl;
    file << "-------------------" << endl;
    file.close();
    return true;
}

int main() {
    string fileA = "matrix_A.txt";
    string fileB = "matrix_B.txt";
    string fileResult = "result_matrix.txt";
    string fileStats = "result_stats.txt";


    vector<double> A, B;

    if (!readMatrix(fileA, A)) return 1;
    if (!readMatrix(fileB, B)) return 1;

    if (A.size() != B.size()) {
        cerr << "Матрицы должны быть одинакового размера" << endl;
        return 1;
    }

    int N = static_cast<int>(sqrt(A.size()));


    vector<double> C(N * N, 0.0);

    auto start = chrono::high_resolution_clock::now();

    multiplyMatrices(A, B, C);

    auto end = chrono::high_resolution_clock::now();
    double timeSec = chrono::duration<double>(end - start).count();

    long long flops = 2LL * N * N * N;

    if (!writeMatrix(fileResult, C)) return 1;
    if (!writeStats(fileStats, N, timeSec, flops)) return 1;

    return 0;
}