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

        print(f"\n{'=' * 60}")
        print(f"{' УРОВЕНЬ L=' + str(L) + ' | РАЗМЕР ОКНА N=' + str(self.window_size) + ' ':^60}")
        print(f"{'=' * 60}")
        print("Вводи биты (0 или 1). Для выхода на выбор L введи 'q'.\n")

    def _print_tape(self, highlight_window=True, leaving_bit_pos=None):
        if not self.tape:
            print("Лента: <пусто>")
            return

        tape_parts = []
        for i, bit in enumerate(self.tape):
            if highlight_window and len(self.tape) >= self.window_size:
                start = len(self.tape) - self.window_size
                if start <= i < len(self.tape):
                    tape_parts.append(f"[{bit}]")
                else:
                    if leaving_bit_pos is not None and i == leaving_bit_pos:
                        tape_parts.append(f"({bit})")  # вытесняемый
                    else:
                        tape_parts.append(f" {bit} ")
            else:
                tape_parts.append(f" {bit} ")

        tape_str = "".join(tape_parts)
        head_spaces = "   " * self.head_position
        print(f"Лента: {tape_str}")
        print(f"Голова:{head_spaces} ↑ (позиция {self.head_position})")

    def process_bit(self, bit: int):
        self.bit_index += 1
        idx = self.bit_index - 1

        print(f"\n{'-' * 50}")
        print(f"Обработка бита {idx} | Ввод: {bit}")
        print(f"{'-' * 50}")

        # Запись бита и сдвиг головы
        self.tape.append(bit)
        self.head_position += 1
        steps = 1

        if len(self.tape) < self.window_size:
            self.current_xor ^= bit
            print("Состояние: окно заполняется")
            self._print_tape(highlight_window=False)
            print(f"Прогресс: {len(self.tape)}/{self.window_size} | Шаги: {steps} | Вывод: 0")
            return

        if len(self.tape) == self.window_size:
            print("СОБЫТИЕ: Окно полностью заполнено!")
            self._print_tape()
            print(f"Текущий XOR окна: {self.current_xor}")
            print(f"Шаги: {steps} | Вывод: {self.current_xor}")
            return

        # Скользящее окно
        leaving_pos = self.head_position - self.window_size
        leaving_bit = self.tape[leaving_pos]
        distance = self.window_size
        steps += distance + 1 + distance

        # Пошаговый XOR
        old_xor = self.current_xor
        after_leaving = old_xor ^ leaving_bit
        new_xor = after_leaving ^ bit

        print(f"Нужно обновить XOR: вытесняется бит на позиции {leaving_pos}")
        self._print_tape(leaving_bit_pos=leaving_pos)

        print(f"\nОбновление XOR поэтапно:")
        print(f"   Старый XOR       : {old_xor}   (из предыдущего окна)")
        print(f" ⊕ Вытесняемый бит  : {leaving_bit}   (позиция {leaving_pos}, уходит из окна)")
        print(f"   =                {after_leaving}")
        print(f" ⊕ Новый бит        : {bit}   (только что записан)")
        print(f"   = Новый XOR      : {new_xor}")

        self.current_xor = new_xor

        is_real_time = steps <= 10
        status = "OK (real-time) ✅" if is_real_time else "FAIL (не real-time) ❌"

        print(f"\nШаги на этом бите: {steps} (1 запись + 2×{distance} перемещений + 1 чтение)")
        print(f"Вывод (XOR окна): {self.current_xor} | Статус: {status}")


# Интерактивный режим
def interactive_mode():
    tm = RealTimeTuringMachine()

    while True:
        try:
            L_input = input("\nВведи уровень L (1–10) или 'q' для выхода: ").strip()
            if L_input.lower() in ['q', 'quit', 'exit']:
                print("До свидания!")
                break
            L = int(L_input)
            if L < 0 or L > 15:
                print("Рекомендую L от 1 до 10")
                continue
            tm.set_L(L)

            while True:
                user_input = input("> ").strip()
                if user_input.lower() in ['q', 'quit', 'exit', '']:
                    print("Возвращаемся к выбору уровня...\n")
                    break
                if user_input not in ['0', '1']:
                    print("Только 0 или 1!")
                    continue
                tm.process_bit(int(user_input))

        except ValueError:
            print("Введи число!")
        except KeyboardInterrupt:
            print("\nВыход.")
            break


if __name__ == "__main__":
    print("=== Машина Тьюринга === ")
    interactive_mode()
