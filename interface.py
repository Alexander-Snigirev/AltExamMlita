import time
import sys
from KUM import KolmogorovUspenskyMachine

class KUMInteractiveInterface:
    def __init__(self):
        self.machine = KolmogorovUspenskyMachine()
        self.inputs_since_build = 0
        self.base_cycle_multiplier = 2.0 

    def print_header(self):
        print("\n" + "="*65)
        print("  KUM: СКОЛЬЗЯЩИЙ ПРЕДИКАТ ЧЕТНОСТИ (XOR)")
        print("  Алгоритм с удвоением окна: N = 1 -> 2 -> 4 -> 8...")
        print("="*65)
        print("Инструкция:")
        print("  0, 1 : Добавить бит")
        print("  !    : Принудительно расширить память (L -> L+1)")
        print("  #    : Выход")
        print("-" * 65)

    def print_state(self, bit, res, msg, cost):
        L = self.machine.current_L
        N = 2**L
        
        full_buffer = self.machine.input_buffer

        if len(full_buffer) < N:

            missing = N - len(full_buffer)
            window_str = "." * missing + "".join(map(str, full_buffer))
            
            status_color = "\033[90m" 
            xor_display = "-"
            status_text = f"Buffering ({len(full_buffer)}/{N})"
            
        else:

            window_bits = full_buffer[-N:]
            window_str = "".join(map(str, window_bits))

            res_color = "\033[92m" if res == 1 else "\033[96m"
            xor_display = f"{res_color}{res}\033[0m"
            status_color = "\033[93m"
            status_text = msg
        print(f" In: {bit} | Win(N={N}): \033[1m[{window_str}]\033[0m -> XOR: {xor_display:<5} | {status_color}{status_text}\033[0m")

    def run(self):
        self.print_header()

        print("Инициализация L=0...")
        self.machine.build_tree_Gamma(0)
        
        while True:
            try:
                N = 2**self.machine.current_L
                prompt = f"\nL={self.machine.current_L} (Окно {N}) > "
                user_input = input(prompt).strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not user_input: continue
            if user_input == '#': break

            if user_input == '!':
                self.expand_memory()
                continue

            for char in user_input:
                if char not in ['0', '1']:
                    print(f" Пропущен символ: {char}")
                    continue

                bit = int(char)
                
                res, msg, cost = self.machine.process_bit_step(bit)
                self.inputs_since_build += 1
                
                self.print_state(bit, res, msg, cost)
                
                current_N = 2**self.machine.current_L
                cycle_limit = int(current_N * self.base_cycle_multiplier) + 4
                
                if self.inputs_since_build >= cycle_limit:
                    print(f"\n\033[90m[Лимит цикла {cycle_limit} достигнут. Расширение...]\033[0m")
                    time.sleep(0.5)
                    self.expand_memory()
                    break 

    def expand_memory(self):
        """Переход к следующему уровню L"""
        next_L = self.machine.current_L + 1
        print(f"\n--- Перестройка Графа Памяти: L={next_L} (Окно N={2**next_L}) ---")
        
        start = time.time()
        self.machine.build_tree_Gamma(next_L)
        dt = time.time() - start
        
        print(f"Построено за {dt:.4f} сек. Узлов: {self.machine.stats['nodes_created']}")

        self.inputs_since_build = 0


if __name__ == "__main__":
    app = KUMInteractiveInterface()
    app.run()