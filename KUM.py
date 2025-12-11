from memory import GraphAddressSpace, MemoryCell
from typing import List, Optional, Dict, Tuple, Any

class KolmogorovUspenskyMachine:
    
    def __init__(self):
        self.memory = GraphAddressSpace()
        self.current_L = 0
        self.operations = 0
        self.trees: Dict[int, MemoryCell] = {}
        self.input_buffer: List[int] = []
        
        
        self.current_path_node: Optional[MemoryCell] = None 
        
        self.stats = {
            'nodes_created': 0,
            'edges_created': 0,
            'traversals': 0
        }

    def init_parameters(self, L: int):
        self.current_L = L
        
        self.current_path_node = None 

    def _collect_leaves(self, node: MemoryCell) -> List[MemoryCell]:
        """Собирает все листья для расширения"""
        leaves = []
        q = [node]
        visited = set()
        while q:
            current = q.pop(0)
            if current.address in visited: continue
            visited.add(current.address)
            
            
            if '0' not in current.pointers and '1' not in current.pointers:
                leaves.append(current)
            else:
                for child in current.pointers.values():
                    if child: q.append(child)
        return leaves

    def copy_subtree(self, node: MemoryCell, xor_mask: int = 0, prefix: str = '') -> MemoryCell:
        """Рекурсивное копирование поддерева. Сохраняем 'path_key'."""
        if node is None: return None

        content = node.content.copy() if node.content else {}
        if 'label' in content:
            content['label'] ^= xor_mask
        
        
        content['path_key'] = prefix 
            
        new_node = self.memory.allocate(content=content)
        self.stats['nodes_created'] += 1
        
        for label, child in node.pointers.items():
            if label not in ['S', 'suf']: 
                if child:
                    
                    new_child = self.copy_subtree(child, xor_mask=xor_mask, prefix=prefix + label)
                    self.memory.add_pointer(new_node.address, label, new_child.address)
                    self.stats['edges_created'] += 1
                    
        return new_node
    
    def _collect_all_nodes(self, node: MemoryCell, path_to_node: Dict[str, MemoryCell], current_path: str):
        """Рекурсивно собирает все узлы и их пути для построения ссылок."""
        if not node: return
        
        
        if 'path_key' in node.content:
             path_to_node[node.content['path_key']] = node
        else:
             path_to_node[current_path] = node

        for label, child in node.pointers.items():
            if child and label not in ['S']:
                
                child_path = current_path + label
                self._collect_all_nodes(child, path_to_node, child_path)

    def _build_suffix_links(self, L: int, root_node: MemoryCell):
        """
        Вспомогательный метод: строит суффиксные ссылки ('S' указатель) 
        для всех узлов. Стоимость O(2^(L+1)) в фазе T_L.
        """
        path_to_node: Dict[str, MemoryCell] = {}
        
        self._collect_all_nodes(root_node, path_to_node, '')
        
        print(f"  Строим O(1) суффиксные ссылки ('S' указатели) для Γ({L}) (Всего {len(path_to_node)} узлов)...")
        
        
        for path_key, node in path_to_node.items():
            if not path_key: continue 
                
            suffix_key = path_key[1:]
            
            
            target_node = path_to_node.get(suffix_key)
            
            if target_node:
                
                self.memory.add_pointer(node.address, 'S', target_node.address)
                self.stats['edges_created'] += 1
            elif not suffix_key:
                
                self.memory.add_pointer(node.address, 'S', root_node.address)
                self.stats['edges_created'] += 1
                
    def build_tree_Gamma(self, L: int):
        """
        Построить дерево Γ(L) с XOR-логикой и суффиксными ссылками.
        Это происходит в фазе T_L.
        """
        print(f"Начинаем построение Γ({L}) (целевая глубина {2**L})...")
        
        if L == 0:
            
            root = self.memory.allocate(content={'label': 0, 'L': 0, 'path_key': ''})
            left = self.memory.allocate(content={'label': 0, 'type': 'leaf', 'path_key': '0'})
            right = self.memory.allocate(content={'label': 1, 'type': 'leaf', 'path_key': '1'})
            
            self.memory.add_pointer(root.address, '0', left.address)
            self.memory.add_pointer(root.address, '1', right.address)
            
            self.trees[0] = root
            self.stats['nodes_created'] += 3
            self.stats['edges_created'] += 2
        else:
            prev_L = L - 1
            base_root = self.copy_subtree(self.trees[prev_L], xor_mask=0, prefix='')
            
            leaves = self._collect_leaves(base_root)
            template_tree = self.trees[prev_L]
            
            for leaf in leaves:
                leaf_val = leaf.content.get('label', 0)
                
                prefix = leaf.content.get('path_key', '')
                extension_root = self.copy_subtree(template_tree, xor_mask=leaf_val, prefix=prefix)

                for label, child_node in extension_root.pointers.items():
                    if label not in ['S']:
                        self.memory.add_pointer(leaf.address, label, child_node.address)
                
                if leaf.content:
                    leaf.content['type'] = 'node'
            
            self.trees[L] = base_root
            self.current_L = L
        
        
        self._build_suffix_links(L, self.trees[L])
            
        print(f"Построено Γ({L}) с суффиксными ссылками.")
        return self.trees[L]
        

    def determine_mode(self, t: int) -> str:
        """Минимальная логика для демонстрации"""
        L = self.current_L
        N = 2**L
        
        
        if L > 0 and L in self.trees and len(self.input_buffer) >= N:
            return 'output'
        return 'idle'

    def process_output_mode(self, t: int) -> int:
        """
        Обработка в режиме вывода: Строго O(1) за счет двух O(1) переходов по указателям.
        """
        L = self.current_L
        route_length = 2**L
        
        if L not in self.trees: return 0
        if len(self.input_buffer) < route_length: return 0
        
        current_bit = self.input_buffer[-1]
        bit_str = str(current_bit)
        
        
        if self.current_path_node is None:
            route = self.input_buffer[-route_length:]
            current = self.trees[L]
            
            
            for bit in route:
                 current = current.pointers.get(str(bit))
                 self.operations += 1
                 self.stats['traversals'] += 1
                 
            self.current_path_node = current
            
            return self.current_path_node.content.get('label', 0) if self.current_path_node and self.current_path_node.content else 0

        current_suffix_root = self.current_path_node.pointers.get('S')
        if current_suffix_root is None:
             return 0
             
        self.operations += 1 
        self.stats['traversals'] += 1

        next_path_node = current_suffix_root.pointers.get(bit_str)
        
        if next_path_node is None: 
            return 0
        
        
        self.current_path_node = next_path_node
        
        self.operations += 1 
        self.stats['traversals'] += 1
        
        
        output = self.current_path_node.content.get('label', 0) if self.current_path_node.content else 0
        
        
        return output
    
    def visualize_tree(self, L: int):
        """
        Визуализирует дерево в консоли с использованием псевдографики.
        Показывает структуру, ребра (0/1) и метки узлов [Val].
        """
        
        if L not in self.trees:
            print(f"Дерево Γ({L}) не построено.")
            return

        root = self.trees[L]
        print(f"\n=== Визуализация Γ({L}), глубина {2**L} ===")
        print(f"Легенда: ── ребро [Метка узла]")
        
        def print_node(node, prefix="", is_last=True, edge_label=None):
            if node is None:
                return

           
            connector = "└── " if is_last else "├── "
            if edge_label is None:
                # Корень
                display_str = ""
            else:
            
                display_str = f"{prefix}{connector}{edge_label} → "

       
            label = node.content.get('label', '?')
            kind = "leaf" if not node.pointers else "node"
            color_reset = "\033[0m"
            color_leaf = "\033[92m" if kind == 'leaf' else ""
            
            print(f"{display_str}{color_leaf}[{label}]{color_reset}")

        
            if edge_label is None:
                child_prefix = ""
            else:
                child_prefix = prefix + ("    " if is_last else "│   ")


            children = []
            if '0' in node.pointers and node.pointers['0']:
                children.append(('0', node.pointers['0']))
            if '1' in node.pointers and node.pointers['1']:
                children.append(('1', node.pointers['1']))


            for i, (e_lbl, child) in enumerate(children):
                is_last_child = (i == len(children) - 1)
                print_node(child, child_prefix, is_last_child, e_lbl)

        print_node(root)
        print("="*40 + "\n")

    def receive_bit(self, bit: int) -> Tuple[int, str]:
        """Принимает бит, обновляет буфер и выполняет шаг машины."""
        self.input_buffer.append(bit)
        t = len(self.input_buffer)
        
        mode = self.determine_mode(t)
        output = 0
        
        if mode == 'output':
            output = self.process_output_mode(t)
        
        return output, mode

    def get_statistics(self) -> Dict[str, Any]:
        return self.stats
    

def test_xor_logic_with_o1_sliding():
    machine = KolmogorovUspenskyMachine()
    
    
    machine.build_tree_Gamma(0)
    machine.build_tree_Gamma(1) 
    machine.build_tree_Gamma(2)
    machine.init_parameters(2) 
    
    
    print("\n" + "="*50)
    print("Тест O(1) скользящего окна (L=2, N=4):")
    
    
    inputs_init = [0, 0, 0, 0]
    initial_ops = machine.operations
    
    for bit in inputs_init:
        machine.receive_bit(bit)
        
    init_cost = machine.operations - initial_ops
    
    print(f"Инициализация: {inputs_init} -> XOR: {machine.current_path_node.content.get('label')} (Cost: {init_cost})")
    print(f"    (Обход O(N) для первого окна - неизбежен для любой машины)")
    
    
    
    
    start_ops = machine.operations
    res, mode = machine.receive_bit(1)
    ops_cost = machine.operations - start_ops
    machine.visualize_tree(2)
    print("-" * 50)

    print(f"Шаг 1: Окно [0001]. XOR: {res} (Cost: {ops_cost} - O(1)) -> OK: {res == 1} (Cost <= 2: {ops_cost <= 2})")

    
    start_ops = machine.operations
    res, mode = machine.receive_bit(0)
    ops_cost = machine.operations - start_ops
    print(f"Шаг 2: Окно [0010]. XOR: {res} (Cost: {ops_cost} - O(1)) -> OK: {res == 1} (Cost <= 2: {ops_cost <= 2})")

    
    start_ops = machine.operations
    res, mode = machine.receive_bit(1)
    ops_cost = machine.operations - start_ops
    print(f"Шаг 3: Окно [0101]. XOR: {res} (Cost: {ops_cost} - O(1)) -> OK: {res == 0} (Cost <= 2: {ops_cost <= 2})")

    
    start_ops = machine.operations
    res, mode = machine.receive_bit(1)
    ops_cost = machine.operations - start_ops
    print(f"Шаг 4: Окно [1011]. XOR: {res} (Cost: {ops_cost} - O(1)) -> OK: {res == 1} (Cost <= 2: {ops_cost <= 2})")

    print("="*50)
    print("В каждом шаге, кроме инициализации, стоимость составляет 2 микро-операции (O(1)).")

if __name__ == "__main__":
    test_xor_logic_with_o1_sliding()    
