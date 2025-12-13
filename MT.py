import math

class RealTimeTuringMachine:
    """
    Эмуляция Машины Тьюринга для вычисления Предиката Григорьева.
    Акцент сделан на подсчете механических шагов (Cost).
    """
    def __init__(self):
        
        self.tape = [] 
        self.head_position = -1
        self.current_xor = 0
        
        
        self.L = 0
        self.window_size = 0 
        
        
        self.total_steps = 0
    
    def set_L(self, L):
        self.L = L
        self.window_size = 2**L
        
        self.tape = []
        self.head_position = -1
        self.current_xor = 0
        self.total_steps = 0
        print(f"\n--- МТ переключена на уровень L={L} (Окно N={self.window_size}) ---")

    def process_bit(self, bit: int) -> dict:
        """
        Принимает бит, обновляет состояние, возвращает стоимость операции.
        """
        
        self.tape.append(bit)
        self.head_position += 1
        steps_this_cycle = 1 
        
        output = 0
        
        
        if len(self.tape) >= self.window_size:
            
            
            target_index = self.head_position - self.window_size
            
            
            
            
            distance = self.head_position - target_index 
            steps_this_cycle += distance
            
            
            x_leaving = self.tape[target_index]
            steps_this_cycle += 1 
            
            
            
            steps_this_cycle += distance
            

            if len(self.tape) == self.window_size:
                
                val = 0
                for b in self.tape: val ^= b
                self.current_xor = val
            else:
                
                self.current_xor = self.current_xor ^ x_leaving ^ bit
            
            output = self.current_xor
            
        else:
            
            output = 0 
            self.current_xor ^= bit
            
        self.total_steps += steps_this_cycle
        
        return {
            'input': bit,
            'output': output,
            'steps': steps_this_cycle,
            'window': self.window_size,
            'is_real_time': steps_this_cycle <= 10 
        }

def compare_machines():
    tm = RealTimeTuringMachine()
    
    
    for L in [1, 2, 3, 5, 10]:
        tm.set_L(L)

        N = 2**L
        inputs = [1] * (N + 2) 
        
        print(f"{'Input Bit':<10} | {'TM Steps (Cost)':<15} | {'KUM Steps':<10} | {'Status'}")
        print("-" * 55)
        
        for i, bit in enumerate(inputs):
            res = tm.process_bit(bit)
            
            
            kum_steps = 1 
            
            
            if i >= N - 1:
                status = "FAIL ❌" if not res['is_real_time'] else "OK ✅"
                print(f"{i:<10} | {res['steps']:<15} | {kum_steps:<10} | {status}")

if __name__ == "__main__":
    compare_machines()
