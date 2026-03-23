import argparse
import matplotlib.pyplot as plt



def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", nargs="?", default="result_stats.txt", 
                        help="Путь к файлу для обработки")
    parser.add_argument("output_file", nargs="?", default="graph.png", 
                        help="Файл для записи результатов")
    return parser.parse_args()


def read_file(input_file):

    data = {"size": [], "cores_used": [], "time_seconds": [], "flops": []}

    try:
        with open(input_file, "r") as file:
            current_block = {}
            
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                
                if not line or line.startswith("-"):
                    if current_block:
                        for key in current_block:
                            if key in data:
                                data[key].append(current_block[key])
                        current_block = {}
                    continue
                
                if ":" in line:
                    try:
                        key, value = line.split(":", 1)
                        key = key.strip().lower()
                        value = value.strip()
                        num_value = float(value)
                        
                        if key == "size":
                            current_block["size"] = int(num_value)
                        # 🔧 ДОБАВЛЕНО: Чтение cores_used или threads
                        elif key in ["cores_used", "threads"]:
                            current_block["cores_used"] = int(num_value)
                        elif key == "time_sec":
                            current_block["time_seconds"] = num_value
                        elif key == "flops":
                            current_block["flops"] = num_value
                            
                    except ValueError:
                        pass
            
            if current_block:
                for key in current_block:
                    if key in data:
                        data[key].append(current_block[key])
                        
        if not data["size"]:
            print(f"Файл {input_file} пуст или имеет неверный формат")
            return None
            
        return data

    except FileNotFoundError:
        print(f"Файл {input_file} не найден")
        return None


def plot_graphs(data, output_file):
    if not data or not data["size"]:
        print("Нет данных для графиков")
        return


    if "cores_used" in data and data["cores_used"]:
        unique_cores = sorted(set(data["cores_used"]))
    else:
        unique_cores = [1] # Если поле cores_used не читается

    plt.figure(figsize=(14, 10))


    plt.subplot(2, 1, 1)
    
    for cores in unique_cores:

        if "cores_used" in data:
            indices = [i for i, c in enumerate(data["cores_used"]) if c == cores]
        else:
            indices = range(len(data["size"]))
            
        sizes = [data["size"][i] for i in indices]
        times = [data["time_seconds"][i] for i in indices]
        

        plt.plot(sizes, times, 'o-', label=f'{cores} ядро(ер)', markersize=4, linewidth=2)

    plt.xlabel("Размер матрицы (N)")
    plt.ylabel("Время (сек)")
    plt.title("Производительность: Время выполнения")
    plt.legend() 
    plt.grid(True, alpha=0.3)

    
    plt.subplot(2, 1, 2)
    
    for cores in unique_cores:
        if "cores_used" in data:
            indices = [i for i, c in enumerate(data["cores_used"]) if c == cores]
        else:
            indices = range(len(data["size"]))
            
        sizes = [data["size"][i] for i in indices]
        flops = [data["flops"][i] for i in indices]
        times = [data["time_seconds"][i] for i in indices]
        

        gflops = [(f / 1e9) / t if t > 0 else 0 for f, t in zip(flops, times)]
        
        plt.plot(sizes, gflops, 's-', label=f'{cores} ядро(ер)', markersize=4, linewidth=2)

    plt.xlabel("Размер матрицы (N)")
    plt.ylabel("Производительность (GFLOPS)")
    plt.title("Эффективность вычислений")
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.suptitle("Анализ умножения матриц (OpenMP)", fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    plt.show()

if __name__ == "__main__":
    args = parse_arguments()
    data = read_file(args.input_file)
    
    if data is not None:
        plot_graphs(data, args.output_file)