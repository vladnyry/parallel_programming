#include <iostream>
#include <vector>
#include <fstream>
#include <chrono>
#include <mpi.h>

using namespace std::chrono;
using namespace std;


vector<int> generate_matrice(int size) {
    vector<int> matrice(size*size);
    for (int i = 0; i < size * size; i++) {
        matrice[i] = (rand() % 10000) / 100;
    }
    return matrice;
}

int main(int argc, char** argv)
{
    int me, nprocs;
    MPI_Init(&argc, &argv);
    MPI_Comm_size(MPI_COMM_WORLD, &nprocs);
    MPI_Comm_rank(MPI_COMM_WORLD, &me);
    vector<int> sizes = { 200,400,800,1200,1600,2000 };
    for (int size : sizes) {
        vector<int> matrices_1(size * size);
        vector<int> matrices_2(size * size);
        matrices_1 = generate_matrice(size);
        matrices_2=generate_matrice(size);
        vector<int> matrice(size * size / nprocs);
        vector<int> matrice_2(size * size,0);
        if (me == 0) {
            cout << "Running program with size = " << size << endl;
            cout << "Execution time(microseconds): ";
        }
        MPI_Scatter(matrices_1.data(), size * size / nprocs, MPI_INT, matrice.data(), size * size / nprocs, MPI_INT, 0, MPI_COMM_WORLD);
        MPI_Bcast(matrices_2.data(), size * size, MPI_INT, 0, MPI_COMM_WORLD);
        MPI_Barrier(MPI_COMM_WORLD);
        auto start = high_resolution_clock::now();
        vector<int> result(size * size / nprocs,0);

        int rows_per_proc = size / nprocs;
        for (int i = 0; i < size / nprocs; i++) {
            for (int j = 0; j < size; j++) {
                int sum = 0;
                for (int k = 0; k < size; k++) {
                    sum += matrice[i * size + k] * matrices_2[k * size + j];
                }
                result[i * size + j] = sum;
            }
        }
        auto stop = high_resolution_clock::now();
        MPI_Gather(result.data(), size * size / nprocs, MPI_INT, matrice_2.data(), size * size / nprocs, MPI_INT, 0, MPI_COMM_WORLD);
        MPI_Barrier(MPI_COMM_WORLD);
        if (me == 0) {
            double seconds = duration_cast<duration<double>>(stop - start).count();
            cout << seconds << endl;
        }
    }
    MPI_Finalize();
}