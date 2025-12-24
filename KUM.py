from memory import GraphAddressSpace, MemoryCell
from typing import List, Optional, Dict, Tuple, Any

class KolmogorovUspenskyMachine:
    """
    Реализация KUM с построением равномерных деревьев и суффиксных ссылок.
    """
    def __init__(self):
        self.memory = GraphAddressSpace()
        self.current_L = 0
        self.operations = 0
        self.trees: Dict[int, MemoryCell] = {}
        self.input_buffer: List[int] = []
        
        
        self.current_path_node: Optional[MemoryCell] = None 
        
        
        self.demo_mode = False

        self.stats = {
            'nodes_created': 0,
            'edges_created': 0,
            'traversals': 0
        }

    def _collect_leaves(self, node: MemoryCell) -> List[MemoryCell]:
        """BFS сбор листьев для расширения дерева"""
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
                for label, child in current.pointers.items():
                    if label in ['0', '1'] and child:
                        q.append(child)
        return leaves

    def _find_nodes_at_depth(self, root: MemoryCell, target_depth: int) -> List[Tuple[List[int], MemoryCell]]:
        """
        Находит все узлы на глубине target_depth и возвращает их 
        вместе с путем (списком битов), который к ним привел.
        """
        results = []
        
        def traverse(node, current_path):
            if len(current_path) == target_depth:
                results.append((list(current_path), node))
                return
            
            for bit in [0, 1]:
                label = str(bit)
                if label in node.pointers:
                    child = node.pointers[label]
                    current_path.append(bit)
                    traverse(child, current_path)
                    current_path.pop()
                    
        traverse(root, [])
        return results

    def copy_and_mask_subtree(self, source_node: MemoryCell, mask_path: List[int]) -> MemoryCell:
        """
        Реализует операцию Г ⊕ А (стр. 4 статьи).
        Копирует дерево, инвертируя метки согласно маске пути А.
        """
        def build_masked(original, depth):
            
            current_mask_bit = mask_path[depth] if depth < len(mask_path) else 0
            
            original_label = original.content.get('label', 0)
            new_label = original_label ^ current_mask_bit
            
            
            new_node = self.memory.allocate(content={'label': new_label})
            self.stats['nodes_created'] += 1
            
            for bit_str in ['0', '1']:
                if bit_str in original.pointers:
                    child = original.pointers[bit_str]
                    new_child = build_masked(child, depth + 1)
                    self.memory.add_pointer(new_node.address, bit_str, new_child.address)
                    self.stats['edges_created'] += 1
            
            return new_node

        return build_masked(source_node, 0)
    
    def _collect_all_nodes(self, node: MemoryCell, path_to_node: Dict[str, MemoryCell], current_path: str):
        """Сбор всех узлов для построения ссылок"""
        if not node: return
        path_key = node.content.get('path_key', current_path)
        path_to_node[path_key] = node
        
        for label, child in node.pointers.items():
            if child and label not in ['S']:
                self._collect_all_nodes(child, path_to_node, path_key + label)

    def _build_suffix_links(self, L: int, root_node: MemoryCell):
        """Построение ссылок 'S' за экспоненциальное время T_L"""
        path_to_node: Dict[str, MemoryCell] = {}
        self._collect_all_nodes(root_node, path_to_node, '')
        
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
        """Индукционное построение по Григорьеву (стр. 5)"""
        if L == 0:
            
            root = self.memory.allocate(content={'label': 0, 'path_key': ''})
            l0 = self.memory.allocate(content={'label': 0, 'path_key': '0'})
            l1 = self.memory.allocate(content={'label': 1, 'path_key': '1'})
            self.memory.add_pointer(root.address, '0', l0.address)
            self.memory.add_pointer(root.address, '1', l1.address)
            self.trees[0] = root
            self.stats['nodes_created'] += 3
        else:
            prev_L = L - 1
            prev_tree = self.trees[prev_L]
            
            new_root = self.copy_and_mask_subtree(prev_tree, []) 
            
            depth_to_reach = 2**prev_L
            leaves_info = self._find_nodes_at_depth(new_root, depth_to_reach)
            
            for path_A, leaf_node in leaves_info:
                
                modified_subtree = self.copy_and_mask_subtree(prev_tree, path_A)
                
                
                for bit_str in ['0', '1']:
                    if bit_str in modified_subtree.pointers:
                        target = modified_subtree.pointers[bit_str]
                        self.memory.add_pointer(leaf_node.address, bit_str, target.address)
            
            self.trees[L] = new_root

        
        self._build_suffix_links(L, self.trees[L])
        self.current_L = L
        self.current_path_node = None 
        return self.trees[L]

    def process_bit_step(self, bit: int) -> Tuple[int, str, int]:
        """
        Обработка одного бита. Возвращает (Результат, Сообщение, Стоимость).
        """
        self.input_buffer.append(bit)
        L = self.current_L
        N = 2**L

        if len(self.input_buffer) < N:
            return 0, "Buffering", 1

        if self.current_path_node is None:
            route = self.input_buffer[-N:]
            current = self.trees[L]
            cost = 0
            for b in route:
                current = current.pointers.get(str(b))
                cost += 1
                if not current: return 0, "Error: Path not found", cost
            
            self.current_path_node = current
            res = current.content.get('label', 0)
            return res, "Init (O(N))", cost

        suffix_node = self.current_path_node.pointers.get('S')
        if not suffix_node: return 0, "Error: S-link missing", 1
        
        
        next_node = suffix_node.pointers.get(str(bit))
        if not next_node: return 0, "Error: Add-link missing", 2
        
        self.current_path_node = next_node
        self.operations += 2
        
        res = next_node.content.get('label', 0)
        return res, "Real-Time (O(1))", 2

    def visualize_tree_ascii(self, L: int):
        """Вывод дерева в консоль"""
        if L not in self.trees: return
        root = self.trees[L]
        print(f"\n--- Граф Памяти Γ({L}), Окно N={2**L} ---")
        
        def print_node(node, prefix="", is_last=True, edge_lbl=None):
            if not node: return
            connector = "└── " if is_last else "├── "
            lbl_str = f"[{node.content.get('label')}]"
            edge_str = f"{edge_lbl} → " if edge_lbl is not None else "[Root] "
            
            
            is_leaf = '0' not in node.pointers and '1' not in node.pointers
            color = "\033[92m" if is_leaf else "" 
            reset = "\033[0m"

            s_link = " (S→...)" if 'S' in node.pointers else ""
            
            print(f"{prefix}{connector}{edge_str}{color}{lbl_str}{s_link}{reset}")
            
            children = []
            for k in ['0', '1']:
                if k in node.pointers and node.pointers[k]:
                    children.append((k, node.pointers[k]))
            
            child_prefix = prefix + ("    " if is_last else "│   ")
            for i, (k, child) in enumerate(children):
                print_node(child, child_prefix, i==len(children)-1, k)

        print_node(root)
        print("-" * 40)
