from memory import GraphAddressSpace, MemoryCell
from typing import List, Optional

class KolmogorovUspenskyMachine:
    """
    Специализированная машина для задачи из статьи Григорьева.
    Реализует построение равномерных деревьев Γ(L) с XOR-логикой меток.
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
        """
        leaves = []
        if not node.pointers:
            return [node]
            
        is_leaf = True

        for label in ['0', '1']:
            if label in node.pointers and node.pointers[label]:
                is_leaf = False
                leaves.extend(self._collect_leaves(node.pointers[label]))
        
        if is_leaf:
            return [node]
        return leaves

    def copy_subtree(self, node: MemoryCell, xor_mask: int = 0, prefix: str = '') -> MemoryCell:
        """
        Рекурсивное копирование поддерева.
        ВАЖНО: Применяет xor_mask к меткам (label) копируемых узлов.
        """
        if node is None:
            return None

        content = node.content.copy() if node.content else {}
        
        if 'label' in content:
            original_label = content['label']
            content['label'] = original_label ^ xor_mask
            
        # Обновляем путь для отладки (не влияет на логику машины)
        if 'path' in content:

            pass 

        new_node = self.memory.allocate(content=content)
        self.stats['nodes_created'] += 1
        
        for label, child in node.pointers.items():
            if child:
                new_child = self.copy_subtree(child, xor_mask=xor_mask, prefix=prefix + label)
                self.memory.add_pointer(new_node.address, label, new_child.address)
                self.stats['edges_created'] += 1
                
        return new_node

    def build_tree_Gamma(self, L: int):
        """
        Построить дерево Γ(L) глубины 2^L.
        Реализует индуктивный переход с XOR-коррекцией меток.
        """
        print(f"Начинаем построение Γ({L}) (целевая глубина {2**L})...")
        
        if L == 0:

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
            prev_L = L - 1
            if prev_L not in self.trees:
                raise ValueError(f"Предыдущее дерево Γ({prev_L}) не найдено!")

            base_root = self.copy_subtree(self.trees[prev_L], xor_mask=0, prefix='')

            leaves = self._collect_leaves(base_root)
            print(f"  В базе Γ({L}) найдено {len(leaves)} листьев для расширения")

            template_tree = self.trees[prev_L]
            
            for leaf in leaves:

                leaf_val = leaf.content.get('label', 0)
            
                extension_root = self.copy_subtree(template_tree, 
                                                   xor_mask=leaf_val, 
                                                   prefix=leaf.content.get('path', ''))

                for label, child_node in extension_root.pointers.items():
                    self.memory.add_pointer(leaf.address, label, child_node.address)

                
                if leaf.content:
                    leaf.content['type'] = 'node'
                    
                    
            self.trees[L] = base_root
            self.root = base_root
            self.current_L = L
            
            print(f"Построено Γ({L}).")

        return self.trees[L]

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


    def receive_bit(self, bit: int):
        self.input_buffer.append(bit)
        t = len(self.input_buffer)
        mode = self.determine_mode(t)
        if mode == 'output':
            return self.process_output_mode(t), 'output'
        elif mode == 'construction':
            self.process_construction_mode(t)
            return 1, 'construction'
        else:
            return 0, 'idle'

    def determine_mode(self, t: int) -> str:

        return 'output' 

    def process_output_mode(self, t: int) -> int:
        L = self.current_L
        route_length = 2**L
        if len(self.input_buffer) < route_length:
            return 0
        route = self.input_buffer[-route_length:]
        if L not in self.trees: return 0
        current = self.trees[L]
        for bit in route:
            bit_str = str(bit)
            if bit_str not in current.pointers: return 0
            current = current.pointers[bit_str]
            if current is None: return 0
            self.operations += 1
            self.stats['traversals'] += 1
        return current.content.get('label', 0) if current.content else 0
        
    def process_construction_mode(self, t: int):
        if self.current_L not in self.trees:
            self.build_tree_Gamma(self.current_L)
            
    def get_statistics(self) -> dict:
        return {
            'nodes_created': self.stats['nodes_created'],
            'traversals': self.stats['traversals'],
            'current_L': self.current_L,
        }

def test_xor_logic():
    machine = KolmogorovUspenskyMachine()
    

    machine.build_tree_Gamma(0)
    machine.visualize_tree(0)
   
    machine.build_tree_Gamma(1)
    machine.visualize_tree(1)
    

    machine.input_buffer = [0, 1]
    res = machine.process_output_mode(2)
    print(f"Путь 01 (Ожидается 1): {res} {'OK' if res==1 else 'FAIL'}")


    machine.input_buffer = [1, 1]
    res = machine.process_output_mode(2)
    print(f"Путь 11 (Ожидается 0): {res} {'OK' if res==0 else 'FAIL'}")

    machine.build_tree_Gamma(2)
    machine.visualize_tree(2)
    
    machine.build_tree_Gamma(3)
    #machine.visualize_tree(3)

    test_path = [1, 0, 1, 1, 0, 0, 1, 1] 
    expected = 1 ^ 0 ^ 1 ^ 1 ^ 0 ^ 0 ^ 1 ^ 1 # = 1
    machine.input_buffer = test_path
    res = machine.process_output_mode(4)
    print(f"Путь {test_path} (Ожидается {expected}): {res} {'OK' if res==expected else 'FAIL'}")

if __name__ == "__main__":
    test_xor_logic()