import time

from KUM import KolmogorovUspenskyMachine


class KUMInteractiveInterface:
    DEMONSTRATION = True  
    
    def __init__(self):
        self.machine = KolmogorovUspenskyMachine()
        self.machine.demo_mode = self.DEMONSTRATION
        self.inputs_since_build = 0
        
        self.phase_duration = 0 

    def print_system(self, msg: str):
        print(f"\033[94m[СИСТЕМА]\033[0m {msg}")

    def print_kum(self, msg: str):
        print(f"\033[93m[КУМ]\033[0m {msg}")

    def run(self):
        print("==================================================")
        print("   ЭМУЛЯТОР МАШИНЫ КОЛМОГОРОВА-УСПЕНСКОГО (KUM)   ")
        print("   Задача: Предикат Четности (XOR) в реальном времени")
        print("==================================================")
        print("Команды:")
        print("  0, 1 : ввод битов")
        print("  #      : выход")
        print("==================================================\n")

        
        self.build_phase(0)

        
        while True:
            try:
                user_input = input(f"\nВвод (L={self.machine.current_L}, N={2**self.machine.current_L}) > ").strip()
            except EOFError:
                break

            if user_input == '#':
                self.print_system("Завершение работы.")
                break
            
            
            if not all(c in '01' for c in user_input):
                self.print_system("Ошибка: вводите только 0 и 1.")
                continue

            
            for char in user_input:
                bit = int(char)
                res, msg, cost = self.machine.process_bit_step(bit)
                
                self.inputs_since_build += 1
                
                
                output_str = f"Вход: {bit} | \033[1mXOR Окна: {res}\033[0m"
                if self.DEMONSTRATION:
                    cost_info = f"(Cost: {cost} ops - {msg})"
                    print(f"{output_str:<30} {cost_info}")
                else:
                    print(output_str)

                
                
                
                cycle_len = 2**(self.machine.current_L + 1) + 2 
                
                if self.inputs_since_build >= cycle_len:
                    self.print_kum("Цикл завершен. Начинается фаза расширения памяти...")
                    self.print_system("Ввод приостановлен (Режим молчания).")
                    time.sleep(1) 
                    
                    next_L = self.machine.current_L + 1
                    self.build_phase(next_L)
                    break 

    def build_phase(self, L: int):
        """Фаза построения: Строит дерево, рисует, сбрасывает счетчики"""
        start_time = time.time()
        self.print_system(f"Построение дерева Γ({L})...")
        
        
        self.machine.build_tree_Gamma(L)
        
        duration = time.time() - start_time
        self.print_system(f"Построение завершено за {duration:.4f} сек.")
        self.print_system(f"Затрачено операций (T_{L}): {self.machine.stats['edges_created']} (Экспоненциально!)")
        
        
        self.machine.visualize_tree_ascii(L)
        
        self.inputs_since_build = 0
        self.print_system("Машина готова к работе в реальном времени.")


if __name__ == "__main__":
    app = KUMInteractiveInterface()
    app.run()