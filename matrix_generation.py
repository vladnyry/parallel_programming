import random
import argparse


def generate_matrix(size, filename):
    """Генерирует матрицу size x size и сохраняет в файл"""

    with open(filename, "w") as f:

        for i in range(size):
            row = []
            for j in range(size):
                num = round(random.uniform(0, 10), 2)
                row.append(str(num))

            f.write(" ".join(row) + "\n")
            

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("size", type=int, help="Размер матрицы")
    parser.add_argument(
        "--output_a", default="matrix_A.txt", help="Имя файла для матрицы A"
    )
    parser.add_argument(
        "--output_b", default="matrix_B.txt", help="Имя файла для матрицы B"
    )
    args = parser.parse_args()
    generate_matrix(args.size, args.output_a)
    generate_matrix(args.size, args.output_b)