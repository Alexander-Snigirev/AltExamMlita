from memory import GraphAddressSpace, MemoryCell
from typing import List, Optional

class KolmogorovUspenskyMachine:
    """
    Специализированная машина для задачи из статьи Григорьева.
    Реализует построение деревьев Γ(L) и обход по маршрутам.
    """
    
    def __init__(self):
        self.memory = GraphAddressSpace()
        self.root = None           # корень текущего дерева Γ(L)
        self.current_L = 0         # текущий уровень дерева
        self.operations = 0        # счётчик операций
        
        self.T = []                # T_i
        self.trees = {}            # Γ(L) -> корень дерева
        self.input_buffer = []     # буфер входных битов
        
        self.stats = {
            'nodes_created': 0,
            'edges_created': 0,
            'traversals': 0
        }

    def init_parameters(self):
        self.T = [10, 50, 200, 800]
        self.build_tree_Gamma(0)
        
    def _collect_leaves(self, node: MemoryCell) -> List[MemoryCell]:
        """
        Вспомогательный метод: найти все листья в поддереве.
        Лист — это узел, у которого нет исходящих ссылок '0' и '1'.
        """
        leaves = []
        if not node.pointers:
            return [node]
            
        is_leaf = True
        for label, child in node.pointers.items():
            if child:
                is_leaf = False
                leaves.extend(self._collect_leaves(child))
        
        if is_leaf:
            return [node]
        return leaves

    def build_tree_Gamma(self, L: int):
        """
        Построить дерево Γ(L) глубины 2^L.
        Удвоение глубины методом наращивания листьев.
        """
        print(f"Начинаем построение Γ({L}) (целевая глубина {2**L})...")
        
        if L == 0:
            # База: Γ(0) глубины 1
            root = self.memory.allocate(content={'label': 0, 'L': 0, 'path': ''})
            left = self.memory.allocate(content={'label': 0, 'type': 'leaf', 'path': '0'})
            right = self.memory.allocate(content={'label': 1, 'type': 'leaf', 'path': '1'})
            
            self.memory.add_pointer(root.address, '0', left.address)
            self.memory.add_pointer(root.address, '1', right.address)
            
            self.trees[0] = root
            self.root = root
            self.stats['nodes_created'] += 3
            self.stats['edges_created'] += 2
            
        else:
           
            base_root = self.copy_subtree(self.trees[L-1], prefix='')

            leaves = self._collect_leaves(base_root)
            print(f"  В Γ({L-1}) найдено {len(leaves)} листьев для расширения")

            
            prev_tree_source = self.trees[L-1]
            
            for leaf in leaves:
                # В статье здесь применяется XOR к меткам, но пока просто копируем структуру
                # prefix для отладки путей
                extension_root = self.copy_subtree(prev_tree_source, prefix=leaf.content.get('path', ''))

                for label, child_node in extension_root.pointers.items():
                    self.memory.add_pointer(leaf.address, label, child_node.address)

                if leaf.content:
                    leaf.content['type'] = 'node'

                    leaf.content['label'] = leaf.content.get('label', 0) ^ extension_root.content.get('label', 0)

            self.trees[L] = base_root
            self.root = base_root
            self.current_L = L
            
            print(f"Построено Γ({L}).")

        return self.trees[L]

    def copy_subtree(self, node: MemoryCell, prefix: str = '') -> MemoryCell:
        """
        Рекурсивное копирование поддерева.
        """
        if node is None:
            return None

       
        content = node.content.copy() if node.content else {}
        
        if 'path' in content:
            
            pass
            
        new_node = self.memory.allocate(content=content)
        self.stats['nodes_created'] += 1
        
        for label, child in node.pointers.items():
            if child:
                new_child = self.copy_subtree(child, prefix + label)
                self.memory.add_pointer(new_node.address, label, new_child.address)
                self.stats['edges_created'] += 1
                
        return new_node
    
    def receive_bit(self, bit: int):
        """
        Принять один входной бит.
        Возвращает пару (output_bit, status).
        """
        self.input_buffer.append(bit)
        t = len(self.input_buffer)
        
        mode = self.determine_mode(t)
        
        if mode == 'output':
            # Режим вывода: используем текущее дерево
            return self.process_output_mode(t), 'output'
        elif mode == 'construction':
            # Режим построения: строим следующее дерево
            self.process_construction_mode(t)
            return 1, 'construction'
        else:
            return 0, 'idle'
    
    def determine_mode(self, t: int) -> str:

        sum_T_prev = sum(self.T[:self.current_L]) if self.current_L > 0 else 0
        sum_T_curr = sum(self.T[:self.current_L + 1])
        
        start_output = sum_T_prev + 2**(self.current_L - 1) if self.current_L > 0 else 0
        end_output = sum_T_prev + 2**self.current_L
        start_construction = end_output
        end_construction = sum_T_curr + 2**self.current_L
        
        if start_output <= t < end_output:
            return 'output'
        elif start_construction <= t < end_construction:
            return 'construction'
        else:
            self.current_L += 1
            return self.determine_mode(t)
        

    def visualize_tree(self, L: int, max_depth: int = 4):
        """
        Визуализировать дерево Γ(L) в ASCII.
        Узлы: [метка]
        Рёбра: 0\ (влево-вниз), 1/ (вправо-вниз)
        """
        if L not in self.trees:
            print(f"Дерево Γ({L}) не построено")
            return
        
        root = self.trees[L]
        print(f"\n=== Дерево Γ({L}), глубина {2**L} ===")
        
        # Рекурсивная функция обхода
        def dfs(node, depth, path, is_left=None):
            if depth > max_depth:
                return []
            
            # Метка узла
            label = node.content.get('label', '?') if node.content else '?'
            
            # Формируем строку для текущего узла
            lines = []
            
            if depth == 0:
                # Корень
                lines.append(f"[{label}]")
            else:
                # Определяем тип ребра
                edge_char = '0\\' if is_left else '1/'
                indent = ' ' * (4 * (depth - 1))
                lines.append(f"{indent}{edge_char}[{label}]")
            
            # Рекурсивно обходим детей
            # Сначала правый потомок (чтобы визуализация была симметричной)
            if '1' in node.pointers and node.pointers['1']:
                child_lines = dfs(node.pointers['1'], depth + 1, path + '1', is_left=False)
                lines.extend(child_lines)
            
            # Затем левый потомок
            if '0' in node.pointers and node.pointers['0']:
                child_lines = dfs(node.pointers['0'], depth + 1, path + '0', is_left=True)
                lines.extend(child_lines)
            
            return lines
        
        tree_lines = dfs(root, 0, '')
        
        for line in tree_lines:
            print(line)
        
        
        print("\nПримеры путей:")
        self.print_sample_paths(root, L)
        
    def print_sample_paths(self, root, L, max_examples=256):
        """Показать несколько примеров путей и их выходов"""
        from itertools import product
        
        # Типа пути длины <=8
        depth = min(8, 2**L)
        paths = list(product([0, 1], repeat=depth))
        
        print(f"Пути длины {depth}:")
        for path in paths[:max_examples]:
            current = root
            path_str = ''.join(str(b) for b in path)
            
            try:
                for bit in path:
                    bit_str = str(bit)
                    if bit_str in current.pointers:
                        current = current.pointers[bit_str]
                    else:
                        break
                
                label = current.content.get('label', '?') if current.content else '?'
                print(f"  {path_str} -> [{label}]")
            except:
                print(f"  {path_str} -> ошибка")

    def process_output_mode(self, t: int) -> int:
        """
        Обработка в режиме вывода.
        Берем маршрут длины 2^{L-1} и идём по дереву Γ(L-1).
        """
        L = self.current_L
        route_length = 2**L
        
        
        if len(self.input_buffer) < route_length:
            return 0
        
        route = self.input_buffer[-route_length:]
        
        if L not in self.trees:
            return 0
        
        current = self.trees[L]
        
        for bit in route:
            bit_str = str(bit)
            
            if bit_str not in current.pointers:
                return 0
            
            next_cell = current.pointers[bit_str]
            
            if next_cell is None:
                return 0
            
            current = next_cell
            self.operations += 1
            self.stats['traversals'] += 1
        if current.content is None:
            print("No leaf")
        return current.content.get('label', 0) if current.content else 0
    
    def process_construction_mode(self, t: int):
        """
        Обработка в режиме построения.
        Строим дерево Γ(current_L).
        """
        if self.current_L not in self.trees:
            print(f"Строим Γ({self.current_L}) в режиме construction...")
            self.build_tree_Gamma(self.current_L)
    
    def get_statistics(self) -> dict:
        """Получить статистику работы машины"""
        return {
            'total_operations': self.operations,
            'nodes_created': self.stats['nodes_created'],
            'edges_created': self.stats['edges_created'],
            'traversals': self.stats['traversals'],
            'current_L': self.current_L,
            'tree_depth': 2**self.current_L if self.current_L in self.trees else 0,
            'memory_cells': len(self.memory.cells)
        }
    

def test_basic():
    """Тест базовой функциональности"""
    machine = KolmogorovUspenskyMachine()
    machine.init_parameters()
    
    print("Тест: строим Γ(0) и Γ(1)")
    machine.build_tree_Gamma(0)
    stats = machine.get_statistics()
    print(f"После Γ(0): {stats}")
    machine.visualize_tree(0)
    
    machine.build_tree_Gamma(1)
    stats = machine.get_statistics()
    print(f"После Γ(1): {stats}")
    machine.visualize_tree(1)

    machine.build_tree_Gamma(2)
    stats = machine.get_statistics()
    print(f"После Γ(2): {stats}")
    machine.visualize_tree(2)

    machine.build_tree_Gamma(3)
    stats = machine.get_statistics()
    print(f"После Γ(3): {stats}")
    machine.visualize_tree(3)
    

    tests4 = [[0,0,0,0],
             [0,0,0,1],
             [0,0,1,0],
             [0,0,1,1],
             [0,1,0,0],
             [0,1,0,1],
             [0,1,1,0],
             [0,1,1,1],
             [1,0,0,0],
             [1,0,0,1],
             [1,0,1,0],
             [1,0,1,1],
             [1,1,0,0],
             [1,1,0,1],
             [1,1,1,0],
             [1,1,1,1]]
    
    tests8 = [[0,0,0,0,0,0,0,1],
             [0,0,1,0,0,0,1,0],
             [0,1,0,0,0,1,0,1],
             [0,1,1,0,0,1,1,1],
             [1,0,0,0,1,0,0,1],
             [1,0,1,0,1,0,1,1],
             [1,1,0,0,1,1,0,1],
             [1,1,1,0,1,1,1,1]]
    # Тест обхода
    print("\nТест обхода:")
    machine.current_L = 3
    for test in tests8:
        machine.input_buffer = test 
        output = machine.process_output_mode(len(machine.input_buffer))
        print(f"Маршрут {machine.input_buffer} -> выход: {output}")
    
    return machine


if __name__ == "__main__":
    '''m = KolmogorovUspenskyMachine()
    m.init_parameters()
    
    # Тестируем глубину
    m.build_tree_Gamma(0) # Глубина 1
    m.visualize_tree(0)
    
    m.build_tree_Gamma(1) # Глубина 2 (1 + 1)
    m.visualize_tree(1)

    m.build_tree_Gamma(2) # Глубина 2 (1 + 1)
    m.visualize_tree(2)'''
    test_basic()