import random
import time
import matplotlib.pyplot as plt
import sys
from typing import List
from KUM import KolmogorovUspenskyMachine

class RealTimeTuringMachine:
    def __init__(self):
        self.tape = []
        self.head_position = -1
        self.current_xor = 0
        self.L = 0
        self.window_size = 0
        self.bit_index = 0

    def set_L(self, L):
        self.L = L
        self.window_size = 2 ** L
        self.tape = []
        self.head_position = -1
        self.current_xor = 0
        self.bit_index = 0

    def process_bit(self, bit: int):
        self.bit_index += 1

        self.tape.append(bit)
        self.head_position += 1
        steps = 1

        if len(self.tape) < self.window_size:
            self.current_xor ^= bit
            return 0

        if len(self.tape) == self.window_size:
            final_xor = self.current_xor ^ bit
            self.current_xor = final_xor
            return final_xor

        leaving_pos = self.head_position - self.window_size
        leaving_bit = self.tape[leaving_pos]
        distance = self.window_size
        steps += distance + 1 + distance

        old_xor = self.current_xor
        after_leaving = old_xor ^ leaving_bit
        new_xor = after_leaving ^ bit

        self.current_xor = new_xor
        return new_xor

    def process(self, bit: int):
        self.process_bit(bit)
        return self.current_xor

    def steps_per_bit(self, bit_index: int) -> int:
        if bit_index <= self.window_size:
            return 1 if bit_index < self.window_size else 2
        else:
            distance = self.window_size
            return 1 + 2 * distance + 1

    def reset_for_benchmark(self):
        self.tape = []
        self.head_position = -1
        self.current_xor = 0
        self.bit_index = 0


def run_benchmark(num_bits: int = 500, max_L: int = 4):
    random.seed(42)
    bits = [random.randint(0, 1) for _ in range(num_bits)]

    print(f"\n{'=' * 80}")
    print(f"АВТОМАТИЧЕСКИЙ БЭНЧМАРК: {num_bits} битов, L от 0 до {max_L}")
    print(f"{'=' * 80}")
    print(
        f"{'L':<4} {'N':<8} {'Время стр. (с)':<18} {'Узлы':<12} {'Оп. KUM (на бит)':<20} {'Шаги МТ (на бит)':<20}")
    print("-" * 80)

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
        tm.set_L(L)
        tm_results = [tm.process(bit) for bit in bits]
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
    tm = RealTimeTuringMachine()
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
