import csv
import argparse
import matplotlib.pyplot as plt
import numpy as np


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", nargs="?", help="Путь к файлу для обработки")
    parser.add_argument("output_file", nargs="?", help="Файл для записи результатов")
    return parser.parse_args()


def read_file(input_file):
    data = {"size": [], "time_seconds": [], "flops": []}

    try:
        with open(input_file, "r") as file:
            current_block = {}
            
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                
                # Пропускаем пустые строки и разделители
                if not line or line.startswith("-"):
                    if current_block:  # Сохраняем завершенный блок
                        for key in current_block:
                            if key in data:
                                data[key].append(current_block[key])
                        current_block = {}
                    continue
                
                # Парсим строки формата "key: value"
                if ":" in line:
                    try:
                        key, value = line.split(":", 1)
                        key = key.strip().lower()
                        value = value.strip()
                        
                        # Преобразуем в число
                        num_value = float(value)
                        
                        # Сопоставляем ключи
                        if key == "size":
                            current_block["size"] = num_value
                        elif key == "time_sec":
                            current_block["time_seconds"] = num_value
                        elif key == "flops":
                            current_block["flops"] = num_value
                            
                    except ValueError as e:
                        print(f"Ошибка в строке {line_num}: неверный формат чисел")
            
            # Не забываем последний блок
            if current_block:
                for key in current_block:
                    if key in data:
                        data[key].append(current_block[key])
                        
        # Проверяем, что данные прочитаны
        if not data["size"]:
            print(f"Файл {input_file} пуст или имеет неверный формат")
            return None
            
        return data

    except FileNotFoundError:
        print(f"Файл {input_file} не найден")
        return None


def plot_graphs(data):
    plt.figure(figsize=(14, 10))

    # 1. График зависимости времени от размера
    plt.subplot(1, 2, 1)
    plt.plot(data["size"], data["time_seconds"])
    plt.xlabel("Размер матрицы")
    plt.ylabel("Время (секунды)")
    plt.title("Зависимость времени от размера")
    plt.grid(True, alpha=0.3)

    # 2. Количество операций
    plt.subplot(1, 2, 2)
    ops_millions = [o / 1e6 for o in data["flops"]]
    plt.plot([str(int(s)) for s in data["size"]], ops_millions)
    plt.xlabel("Размер матрицы")
    plt.ylabel("Операции (миллионы)")
    plt.title("Количество операций")
    plt.grid(True, alpha=0.3, axis="y")
    plt.suptitle("Анализ умножения матриц", fontsize=16)
    plt.savefig(args.output_file, dpi=150, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    args = parse_arguments()
    data = read_file(args.input_file)
    plot_graphs(data)