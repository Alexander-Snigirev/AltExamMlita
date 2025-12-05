class MemoryCell:
    """Ячейка памяти в графовой архитектуре"""
    def __init__(self, address):
        self.address = address
        self.content = None      
        self.pointers = {}       
        self.tags = set()        
        
    def add_pointer(self, label, target_cell):
        """Добавить ссылку с меткой label на другую ячейку"""
        self.pointers[label] = target_cell
        
    def follow(self, label):
        """Перейти по ссылке с меткой label"""
        if label in self.pointers:
            return self.pointers[label]
        return None
        
    def __repr__(self):
        ptrs = list(self.pointers.keys())
        return f"Cell({self.address}, content={self.content}, ptrs={ptrs})"


class GraphAddressSpace:
    """
    Адресное пространство как произвольный граф.
    Аналог "памяти" в модели Колмогорова-Успенского.
    """
    
    def __init__(self):
        self.cells = {}           
        self.next_address = 0
        self.active_cells = set() 
        self.access_cost = 1      
        
    def allocate(self, content=None):
        """Выделить новую ячейку памяти"""
        addr = self.next_address
        cell = MemoryCell(addr)
        cell.content = content
        self.cells[addr] = cell
        self.next_address += 1
        return cell
    
    def get_cell(self, address):
        """Получить ячейку по адресу"""
        return self.cells.get(address)
    
    def add_pointer(self, from_addr, label, to_addr):
        """Создать ссылку между ячейками"""
        from_cell = self.get_cell(from_addr)
        to_cell = self.get_cell(to_addr)
        if from_cell and to_cell:
            from_cell.add_pointer(label, to_cell)
            
    def follow_pointer(self, from_addr, label):
        """Перейти по ссылке из ячейки"""
        cell = self.get_cell(from_addr)
        if cell and label in cell.pointers:
            target = cell.pointers[label]
            return target.address, target.content
        return None, None
    
    def set_active(self, address):
        """Добавить ячейку в активную зону"""
        cell = self.get_cell(address)
        if cell:
            self.active_cells.add(cell)
            
    def get_active_zone(self, max_distance=3):
        """
        Получить активную зону: все ячейки, достижимые из 
        текущих активных за max_distance переходов.
        """
        if not self.active_cells:
            return set()
            
        zone = set(self.active_cells)
        frontier = list(self.active_cells)
        
        for _ in range(max_distance):
            new_frontier = []
            for cell in frontier:
                for neighbor in cell.pointers.values():
                    if neighbor not in zone:
                        zone.add(neighbor)
                        new_frontier.append(neighbor)
            frontier = new_frontier
            if not frontier:
                break
                
        return zone
    
    def simulate_access_cost(self, from_addr, to_addr):
        """
        В идеализированной модели Колмогорова доступ всегда стоит 1,
        независимо от "расстояния" в графе.
        Но мы можем эмулировать разные стратегии.
        """
        
        
        
        from_cell = self.get_cell(from_addr)
        to_cell = self.get_cell(to_addr)
        
        if not from_cell or not to_cell:
            return float('inf')
            
        
        for label, target in from_cell.pointers.items():
            if target.address == to_addr:
                return self.access_cost  
                
        
        
        visited = set()
        queue = [(from_cell, 0)]
        
        while queue:
            cell, distance = queue.pop(0)
            if cell.address == to_addr:
                return distance + 1  
                
            visited.add(cell.address)
            for neighbor in cell.pointers.values():
                if neighbor.address not in visited:
                    queue.append((neighbor, distance + 1))
                    
        return float('inf')  
    
    def __repr__(self):
        return f"GraphAddressSpace(cells={len(self.cells)}, active={len(self.active_cells)})"



def demo_memory():
    """Демонстрация работы адресного пространства"""
    mem = GraphAddressSpace()
    
    
    root = mem.allocate(content="root")
    left = mem.allocate(content="left")
    right = mem.allocate(content="right")
    
    print(f"Выделили ячейки: {root.address}, {left.address}, {right.address}")
    
    
    mem.add_pointer(root.address, "0", left.address)
    mem.add_pointer(root.address, "1", right.address)
    
    
    mem.set_active(root.address)
    
    
    addr1, content1 = mem.follow_pointer(root.address, "0")
    print(f"По ссылке '0' из {root.address}: адрес {addr1}, содержимое '{content1}'")
    
    addr2, content2 = mem.follow_pointer(root.address, "1")
    print(f"По ссылке '1' из {root.address}: адрес {addr2}, содержимое '{content2}'")
    
    
    zone = mem.get_active_zone(max_distance=2)
    print(f"Активная зона (макс. расстояние 2): {[c.address for c in zone]}")
    
    
    cost = mem.simulate_access_cost(root.address, left.address)
    print(f"Стоимость перехода root->left: {cost} (в идеальной модели должно быть 1)")
    
    return mem


if __name__ == "__main__":
    demo_memory()