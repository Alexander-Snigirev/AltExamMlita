import random
import time
import matplotlib.pyplot as plt
import sys
from typing import List
from KUM import KolmogorovUspenskyMachine
from MT import RealTimeTuringMachine

def run_benchmark(num_bits: int = 500, max_L: int = 4):
    random.seed(42)
    bits = [random.randint(0, 1) for _ in range(num_bits)]

    print(f"\n{'=' * 80}")
    print(f"АВТОМАТИЧЕСКИЙ БЭНЧМАРК: {num_bits} битов, L от 0 до {max_L}")
    print(f"{'=' * 80}")
    print(
        f"{'L':<4} {'N':<8} {'Время стр. (с)':<18} {'Узлы':<12} {'Оп. KUM (на бит)':<20} {'Шаги МТ (на бит)':<20}")
    print("-" * 95)

    L_values = list(range(max_L + 1))
    build_times = []
    nodes_list = []
    kum_ops_avg = []
    tm_steps_avg = []

    for L in L_values:
        N = 1 << L
        kum = KolmogorovUspenskyMachine()
        kum.demo_mode = False
        start = time.time()
        for level in range(L + 1):
            if level not in kum.trees:
                kum.build_tree_Gamma(level)
        build_time = time.time() - start

        kum_results = []
        kum_ops_total = 0
        inputs_since_build = 0
        for bit in bits:
            xor_val, _, cost = kum.process_bit_step(bit)
            inputs_since_build += 1

            if inputs_since_build <= 2 ** L:
                xor_val = 0

            kum_results.append(xor_val)
            kum_ops_total += cost

        tm = RealTimeTuringMachine()
        # В MT.py метод set_L выводит много текста в консоль
        tm.set_L(L)
        tm_results = [tm.process_bit(bit) for bit in bits]  # В MT.py метод называется process_bit

        real_time_bits = max(1, num_bits - N)
        avg_kum = kum_ops_total / real_time_bits
        avg_tm = sum(tm.steps_per_bit(i + 1) for i in range(num_bits)) / real_time_bits

        print(
            f"{L:<4} {N:<8} {build_time:<18.4f} {kum.stats['nodes_created']:<12} {avg_kum:<20.2f} {avg_tm:<20.2f} ")

        build_times.append(build_time)
        nodes_list.append(kum.stats['nodes_created'])
        kum_ops_avg.append(avg_kum)
        tm_steps_avg.append(avg_tm)
    plt.figure(figsize=(12, 5))

    plt.subplot(1, 2, 1)
    plt.plot(L_values, kum_ops_avg, 'o-g', label='Операции KUM на бит (O(1))', linewidth=3, markersize=10)
    plt.plot(L_values, tm_steps_avg, 's-r', label='Шаги МТ на бит (O(N))', linewidth=3, markersize=10)
    plt.xlabel('Уровень L')
    plt.ylabel('Операции / шаги на бит')
    plt.title('Скорость обработки одного бита')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(L_values)

    plt.subplot(1, 2, 2)
    plt.plot(L_values, build_times, '^-b', label='Время строительства (с)', linewidth=3, markersize=10)
    plt.plot(L_values, nodes_list, 'd-m', label='Число узлов', linewidth=3, markersize=10)
    plt.yscale('log')
    plt.xlabel('Уровень L')
    plt.ylabel('Время (с) / Узлы (лог. шкала)')
    plt.title('Препроцессинг KUM')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(L_values)
    for i, n in enumerate(nodes_list):
        plt.annotate(f'{n}', (L_values[i], n), textcoords="offset points", xytext=(0,10), ha='center')

    plt.tight_layout()
    plt.show()

def interactive_compare():
    tm = RealTimeTuringMachine(verbose=False)
    kum = KolmogorovUspenskyMachine()
    kum.demo_mode = False

    print("=" * 70)
    print("   СРАВНЕНИЕ МАШИНЫ ТЬЮРИНГА И МАШИНЫ КОЛМОГОРОВА–УСПЕНСКОГО")
    print("   Задача: скользящий XOR последних 2^L бит (предикат Григорьева)")
    print("=" * 70)

    while True:
        inp = input("\nВведи L (до 4–5) или 'q': ").strip()
        if inp.lower() in ['q', 'quit']:
            break
        try:
            L = int(inp)
        except:
            continue

        N = 1 << L
        print(f"\n{'='*20} L = {L} | N = {N} {'='*20}")
        tm.set_L(L)

        start = time.time()
        print("Строим Γ(L)...")
        for level in range(L + 1):
            if level not in kum.trees:
                kum.build_tree_Gamma(level)
        print(f"Готово за {time.time() - start:.2f}с, узлов: {kum.stats['nodes_created']}")

        if L <= 3:
            kum.visualize_tree_ascii(L)

        print("\nВводи биты (0/1), 'q' — выйти")
        bit_count = 0
        while True:
            user_in = input("> ").strip()
            if user_in.lower() in ['q', '']:
                break
            if user_in not in ['0', '1']:
                continue
            bit = int(user_in)
            bit_count += 1

            tm_xor = tm.process(bit)
            kum_xor, msg, cost = kum.process_bit_step(bit)

            steps_mt = tm.steps_per_bit(bit_count)
            status_mt = "real-time" if steps_mt <= 10 else "НЕ real-time"
            print(f"\nБит {bit_count}: {bit}")
            if bit_count< N:
                print(f"   МТ: XOR = 0 | Шаги ≈ {steps_mt} | {status_mt}")
            else:
                print(f"   МТ: XOR = {tm_xor} | Шаги ≈ {steps_mt} | {status_mt}")
            print(f"   КУМ: XOR = {kum_xor} | Оп. = {cost} | {msg}")
            if bit_count >= N and tm_xor == kum_xor:
                print("   ✓ Совпадает")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--benchmark":
        run_benchmark(num_bits=500, max_L=4)
    else:
        interactive_compare()
