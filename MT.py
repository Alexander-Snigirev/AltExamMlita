class RealTimeTuringMachine:
    def __init__(self):
        self.tape = []
        self.head_position = -1
        self.L = 0
        self.window_size = 0
        self.bit_index = 0

    def set_L(self, L: int):
        self.L = L
        self.window_size = 2 ** L
        self.tape = []
        self.head_position = -1
        self.bit_index = 0

        print(f"\n{'=' * 70}")
        print(f" МАШИНА ТЬЮРИНГА — ПРЕДЕЛЫ REAL-TIME ".center(70))
        print(f" УРОВЕНЬ L = {L} | ОКНО N = {self.window_size} ".center(70))
        print(f"{'=' * 70}")
        print("Вычисляем метку в дереве Γ(L) по последнему окну битов.")
        print("Ввод битов: 0 или 1. 'q' или пусто — назад.\n")

    def _print_tape(self):
        if not self.tape:
            print("Лента: <пусто>")
            return

        tape_str = ""
        start_window = max(0, len(self.tape) - self.window_size)
        for i, bit in enumerate(self.tape):
            if i >= start_window:
                tape_str += f"[{bit}]"
            else:
                tape_str += f" {bit} "
        head_spaces = "   " * self.head_position
        print(f"Лента: {tape_str}")
        print(f"Голова: {head_spaces}↑ (позиция {self.head_position})")

    def _recursive_D(self, level: int, path: str) -> str:
        """Д_Γ(level)(path) по Григорьеву"""
        if level == 0:
            return path

        prev_level = level - 1
        prev_N = 2 ** prev_level
        A = path[:prev_N]
        B = path[prev_N:]

        D_A = self._recursive_D(prev_level, A)
        D_B = self._recursive_D(prev_level, B)

        # Побитовый XOR D_B ⊕ A
        D_B_xored = ''.join(str(int(D_B[i]) ^ int(A[i])) for i in range(prev_N))

        return D_A + D_B_xored

    def show_calculation(self, window_bits: str):
        print("\nРасчёт предиката:")
        full_D = self._recursive_D(self.L, window_bits)

        if self.L >= 1:
            prev_N = 2 ** (self.L - 1)
            A = window_bits[:prev_N]
            B = window_bits[prev_N:]
            D_A = self._recursive_D(self.L - 1, A)
            D_B = self._recursive_D(self.L - 1, B)
            D_B_xored = ''.join(str(int(D_B[i]) ^ int(A[i])) for i in range(prev_N))

            print(f"A = {A} | B = {B}")
            print(f"Д_{self.L-1}(A) = {D_A}")
            print(f"Д_{self.L-1}(B) = {D_B}")
            print(f"Д_{self.L-1}(B) ⊕ A = {D_B_xored}")
            print(f"Полное Д_{self.L} = {full_D}")
        else:
            print(f"Д_0 = {window_bits}")

        metka = int(full_D[-1])
        print(f"Метка листа = {metka}")
        print(f"Предикат P(A) = (метка == 0): {metka == 0}\n")

    def process_bit(self, bit: int):
        self.bit_index += 1
        print(f"\n--- Бит №{self.bit_index}: {bit} ---")

        self.tape.append(bit)
        self.head_position += 1

        self._print_tape()

        if len(self.tape) < self.window_size:
            print("Окно заполняется — вывод 1 (фаза вне окна)")
            return

        window_bits = ''.join(map(str, self.tape[-self.window_size:]))
        print(f"Окно: {window_bits}")

        if self.L > 4:
            print("L > 4 → экспоненциальная рекурсия!")
            print("МТ НЕ может вычислить в real-time ❌")
            print("Требуется ~2^{2^L} операций")
        else:
            self.show_calculation(window_bits)

            steps = 2 ** (2 ** self.L)
            print(f"Примерные шаги: ~{steps}")
            if self.L >= 3:
                print("Уже НЕ real-time для сложной функции ❌")
            else:
                print("Для малого L — ещё возможно")

# Интерактивный запуск
def interactive_turing_machine():
    tm = RealTimeTuringMachine()

    while True:
        try:
            L_input = input("\nВведите L (0–6): ").strip()
            if L_input.lower() in ['q', 'quit', 'exit', '']:
                print("Выход.")
                break
            try:
                L = int(L_input)
                tm.set_L(L)
            except ValueError:
                print("Число!")
                continue

            while True:
                user_input = input("> ").strip()
                if user_input.lower() in ['q', 'quit', 'exit', '']:
                    break
                if user_input not in ['0', '1']:
                    print("0 или 1!")
                    continue
                tm.process_bit(int(user_input))

        except KeyboardInterrupt:
            print("\nВыход.")
            break


if __name__ == "__main__":
    print("=== ДЕМОНСТРАЦИЯ: МАШИНА ТЬЮРИНГА ===")
    interactive_turing_machine()
