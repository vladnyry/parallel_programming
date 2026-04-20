#!/usr/bin/env python3
"""Анализ и визуализация результатов MPI-экспериментов."""

import argparse
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

def parse_arguments():
    parser = argparse.ArgumentParser(description="Визуализация результатов умножения матриц на MPI")
    parser.add_argument("input_file", nargs="?", default="result_stats_mpi.txt", 
                       help="Файл со статистикой (по умолчанию: result_stats_mpi.txt)")
    parser.add_argument("output_file", nargs="?", default="results_plot.png", 
                       help="Файл для сохранения графика (по умолчанию: results_plot.png)")
    parser.add_argument("--show", action="store_true", help="Показать графики на экране")
    return parser.parse_args()

def read_file(input_file):
    """Читает файл статистики и возвращает список записей."""
    records = []
    
    try:
        with open(input_file, "r", encoding="utf-8") as file:
            current = {}
            
            for line in file:
                line = line.strip()
                
                # Пропускаем пустые строки и разделители
                if not line or line.startswith("-"):
                    if current and "size" in current and "time_sec" in current:
                        records.append(current)
                    current = {}
                    continue
                
                # Парсим "key: value"
                if ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) != 2:
                        continue
                    
                    key = parts[0].strip().lower()
                    value = parts[1].strip()
                    
                    # Обрабатываем составные значения: "size: 400 | procs: 4"
                    if "|" in value:
                        for sub in value.split("|"):
                            if ":" in sub:
                                k, v = sub.strip().split(":", 1)
                                k = k.strip().lower()
                                v = v.strip()
                                try:
                                    current[k] = int(v) if k in ["size", "procs", "processes"] else float(v)
                                except ValueError:
                                    current[k] = v
                    else:
                        try:
                            current[key] = int(value) if key in ["size", "procs", "processes"] else float(value)
                        except ValueError:
                            current[key] = value
            
            # Последний блок
            if current and "size" in current and "time_sec" in current:
                records.append(current)
                        
        if not records:
            print(f"⚠️  Файл {input_file} пуст или имеет неверный формат")
            return None
            
        print(f"✅ Загружено {len(records)} записей из {input_file}")
        return records

    except FileNotFoundError:
        print(f"❌ Файл {input_file} не найден")
        return None
    except Exception as e:
        print(f"❌ Ошибка чтения: {e}")
        return None

def calculate_metrics(records):
    """Вычисляет speedup и efficiency для каждой записи."""
    # Группируем по размеру матрицы
    by_size = defaultdict(list)
    for r in records:
        by_size[r["size"]].append(r)
    
    results = []
    for size, entries in by_size.items():
        # Находим базовое время (1 процесс)
        base_time = None
        for e in entries:
            p = e.get("procs") or e.get("processes") or 1
            if p == 1:
                base_time = e["time_sec"]
                break
        
        for e in entries:
            p = e.get("procs") or e.get("processes") or 1
            t = e["time_sec"]
            flops = e.get("flops", 2 * size**3)
            
            entry = {
                "size": size,
                "procs": p,
                "time": t,
                "flops": flops,
                "gflops": flops / t / 1e9 if t > 0 else 0,
                "speedup": base_time / t if base_time and t > 0 else None,
                "efficiency": (base_time / t / p * 100) if base_time and t > 0 and p > 0 else None
            }
            results.append(entry)
    
    return results

def print_summary(records):
    """Выводит текстовую сводку в консоль."""
    print("\n" + "=" * 80)
    print("📊 СВОДКА РЕЗУЛЬТАТОВ")
    print("=" * 80)
    print(f"{'Size':<8} {'Procs':<8} {'Time(s)':<12} {'GFLOPS':<12} {'Speedup':<10} {'Eff(%)':<10}")
    print("-" * 80)
    
    for r in sorted(records, key=lambda x: (x["size"], x["procs"])):
        su = f"{r['speedup']:.2f}×" if r["speedup"] else "N/A"
        ef = f"{r['efficiency']:.1f}%" if r["efficiency"] else "N/A"
        print(f"{r['size']:<8} {r['procs']:<8} {r['time']:<12.4f} {r['gflops']:<12.2f} {su:<10} {ef:<10}")
    
    print("=" * 80)

def plot_graphs(records, output_file, show=False):
    """Строит 4 графика: время, ускорение, эффективность, производительность."""
    
    # Группируем данные
    sizes = sorted(set(r["size"] for r in records))
    procs_list = sorted(set(r["procs"] for r in records))
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Анализ параллельного умножения матриц (MPI)', fontsize=16, fontweight='bold')
    
    colors = plt.cm.viridis(np.linspace(0, 1, len(sizes)))
    
    # === График 1: Время выполнения от размера матрицы ===
    ax = axes[0, 0]
    for p in procs_list:
        points = [(r["size"], r["time"]) for r in records if r["procs"] == p]
        if points:
            sizes_p, times = zip(*sorted(points))
            ax.plot(sizes_p, times, 'o-', label=f'{p} proc(s)', markersize=4)
    ax.set_xlabel('Размер матрицы (N×N)', fontsize=10)
    ax.set_ylabel('Время выполнения (секунды)', fontsize=10)
    ax.set_title('⏱️ Зависимость времени от размера матрицы', fontsize=11, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(fontsize=9)
    ax.set_xscale('log')
    ax.set_yscale('log')
    
    # === График 2: Ускорение (Speedup) ===
    ax = axes[0, 1]
    for N in sizes:
        points = [(r["procs"], r["speedup"]) for r in records 
                 if r["size"] == N and r["speedup"] is not None]
        if points:
            procs, speeds = zip(*sorted(points))
            ax.plot(procs, speeds, 's--', label=f'N={N}', markersize=5)
            # Идеальное ускорение (линия y=x)
            ax.plot(procs, procs, 'k:', alpha=0.4, linewidth=1, label='Идеал (линейное)' if N == sizes[0] else "")
    ax.set_xlabel('Количество процессов', fontsize=10)
    ax.set_ylabel('Ускорение (S = T₁ / Tₚ)', fontsize=10)
    ax.set_title('🚀 Ускорение параллелизации', fontsize=11, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(fontsize=8)
    
    # === График 3: Эффективность (%) ===
    ax = axes[1, 0]
    for N in sizes:
        points = [(r["procs"], r["efficiency"]) for r in records 
                 if r["size"] == N and r["efficiency"] is not None]
        if points:
            procs, effs = zip(*sorted(points))
            ax.plot(procs, effs, 'd-.', label=f'N={N}', markersize=5)
    ax.axhline(y=100, color='gray', linestyle=':', alpha=0.5, label='100% (идеал)')
    ax.set_xlabel('Количество процессов', fontsize=10)
    ax.set_ylabel('Эффективность (%)', fontsize=10)
    ax.set_title('📈 Эффективность использования ядер', fontsize=11, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(fontsize=8)
    ax.set_ylim(0, 110)
    
    # === График 4: Производительность (GFLOPS) ===
    ax = axes[1, 1]
    for p in procs_list:
        points = [(r["size"], r["gflops"]) for r in records if r["procs"] == p]
        if points:
            sizes_p, gflops = zip(*sorted(points))
            ax.plot(sizes_p, gflops, '^-', label=f'{p} proc(s)', markersize=4)
    ax.set_xlabel('Размер матрицы (N×N)', fontsize=10)
    ax.set_ylabel('Производительность (GFLOPS)', fontsize=10)
    ax.set_title('⚡ Вычислительная мощность', fontsize=11, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(fontsize=9)
    ax.set_xscale('log')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"💾 Графики сохранены: {output_file}")
    
    if show:
        plt.show()
    else:
        plt.close()

def main():
    args = parse_arguments()
    
    print(f"📥 Чтение данных из: {args.input_file}")
    records = read_file(args.input_file)
    
    if not records:
        print("❌ Не удалось загрузить данные")
        return 1
    
    # Вычисляем метрики
    metrics = calculate_metrics(records)
    
    # Печатаем сводку
    print_summary(metrics)
    
    # Строим графики
    plot_graphs(metrics, args.output_file, show=args.show)
    
    # Ключевые выводы
    print("\n🎯 Ключевые выводы:")
    
    # Находим лучшее ускорение
    best = max((r for r in metrics if r["speedup"]), key=lambda x: x["speedup"] if x["speedup"] else 0)
    if best["speedup"]:
        print(f"   • Максимальное ускорение: {best['speedup']:.2f}× при N={best['size']}, P={best['procs']}")
    
    # Находим лучшую эффективность
    best_eff = max((r for r in metrics if r["efficiency"]), key=lambda x: x["efficiency"] if x["efficiency"] else 0)
    if best_eff["efficiency"]:
        print(f"   • Лучшая эффективность: {best_eff['efficiency']:.1f}% при N={best_eff['size']}, P={best_eff['procs']}")
    
    # Находим пиковую производительность
    best_gflops = max(metrics, key=lambda x: x["gflops"])
    print(f"   • Пиковая производительность: {best_gflops['gflops']:.2f} GFLOPS при N={best_gflops['size']}, P={best_gflops['procs']}")
    
    print(f"\n✅ Готово! Открой {args.output_file} для просмотра графиков.")
    return 0

if __name__ == "__main__":
    exit(main())