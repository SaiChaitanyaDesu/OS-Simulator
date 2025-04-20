import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
import random
import numpy as np
from collections import deque

class MemoryAllocator:
    def __init__(self, total_memory=2048, partition_size=100):
        self.total_memory = total_memory
        self.partition_size = partition_size
        self.memory_blocks = []
        self.process_history = []
        self.performance_metrics = {
            'First Fit': {'allocations': 0, 'avg_time': 0, 'total_time': 0},
            'Next Fit': {'allocations': 0, 'avg_time': 0, 'total_time': 0, 'last_position': 0},
            'Best Fit': {'allocations': 0, 'avg_time': 0, 'total_time': 0, 'last_position': 0},
            'Worst Fit': {'allocations': 0, 'avg_time': 0, 'total_time': 0, 'last_position': 0}
        }
        self.current_algorithm = 'First Fit'
        self.memory_usage_history = []
        self.operation_history = []
        self.log_messages = []
        self.reset_memory()
    
    def reset_memory(self):
        """Initialize memory blocks with equal partitions"""
        self.memory_blocks = [
            {
                'id': i+1,
                'total_size': self.partition_size,
                'allocated_size': 0,
                'process_id': None,
                'fragmentation': 0,
                'status': 'Free'
            } 
            for i in range(self.total_memory // self.partition_size)
        ]
        # Reset all last positions
        for algo in self.performance_metrics:
            self.performance_metrics[algo]['last_position'] = 0
        self.process_history = []
        self.memory_usage_history = [0]
        self.log_messages.append("Memory reset to initial state")
        self.update_metrics()
    
    def update_metrics(self):
        """Calculate current memory statistics"""
        self.allocated_memory = sum(block['allocated_size'] for block in self.memory_blocks)
        self.free_memory = self.total_memory - self.allocated_memory
        self.internal_frag = sum(block['fragmentation'] for block in self.memory_blocks)
        
        # Calculate external fragmentation
        free_blocks = [block['total_size'] for block in self.memory_blocks if block['status'] == 'Free']
        if free_blocks:
            max_free = max(free_blocks)
            self.external_frag = sum(free_blocks) - max_free
        else:
            self.external_frag = 0
            
        self.utilization = (self.allocated_memory / self.total_memory) * 100
        self.memory_usage_history.append(self.utilization)
    
    def first_fit(self, process_size, process_id):
        """First Fit allocation algorithm that properly considers remaining spaces"""
        start_time = time.perf_counter()
        for i, block in enumerate(self.memory_blocks):
            remaining = block['total_size'] - block['allocated_size']
            if remaining >= process_size:
                self._allocate_block(i, process_size, process_id)
                elapsed = (time.perf_counter() - start_time) * 1000  # ms
                self._update_performance('First Fit', elapsed)
                self.performance_metrics['First Fit']['last_position'] = i
                self.log_messages.append(
                    f"First Fit: Allocated P{process_id} ({process_size}KB) to Block {i+1} "
                    f"(Remaining: {remaining}KB)"
                )
                return True
        
        self.log_messages.append(
            f"First Fit: Failed to allocate P{process_id} ({process_size}KB) - no suitable block found"
        )
        return False
    
    def next_fit(self, process_size, process_id):
        """Next Fit that remembers position across all operations"""
        start_time = time.perf_counter()
        n = len(self.memory_blocks)
        
        # Get the last position from any algorithm's last allocation
        last_pos = 0
        for algo in self.performance_metrics:
            if self.performance_metrics[algo]['last_position'] > last_pos:
                last_pos = self.performance_metrics[algo]['last_position']
        
        # Search from last position to end
        for i in range(last_pos, n):
            block = self.memory_blocks[i]
            remaining = block['total_size'] - block['allocated_size']
            if remaining >= process_size:
                self._allocate_block(i, process_size, process_id)
                self.performance_metrics['Next Fit']['last_position'] = (i + 1) % n
                elapsed = (time.perf_counter() - start_time) * 1000  # ms
                self._update_performance('Next Fit', elapsed)
                self.log_messages.append(
                    f"Next Fit: Allocated P{process_id} ({process_size}KB) to Block {i+1} "
                    f"(Remaining: {remaining}KB)"
                )
                return True
        
        # Search from beginning to last position
        for i in range(0, last_pos):
            block = self.memory_blocks[i]
            remaining = block['total_size'] - block['allocated_size']
            if remaining >= process_size:
                self._allocate_block(i, process_size, process_id)
                self.performance_metrics['Next Fit']['last_position'] = (i + 1) % n
                elapsed = (time.perf_counter() - start_time) * 1000  # ms
                self._update_performance('Next Fit', elapsed)
                self.log_messages.append(
                    f"Next Fit: Allocated P{process_id} ({process_size}KB) to Block {i+1} "
                    f"(Remaining: {remaining}KB)"
                )
                return True
        
        self.log_messages.append(
            f"Next Fit: Failed to allocate P{process_id} ({process_size}KB) - no suitable block found"
        )
        return False
    
    def best_fit(self, process_size, process_id):
        """Best Fit that properly finds smallest adequate block"""
        start_time = time.perf_counter()
        best_block_idx = -1
        min_diff = float('inf')
        
        for i, block in enumerate(self.memory_blocks):
            remaining = block['total_size'] - block['allocated_size']
            if remaining >= process_size:
                diff = remaining - process_size
                if diff < min_diff:
                    min_diff = diff
                    best_block_idx = i
        
        if best_block_idx != -1:
            self._allocate_block(best_block_idx, process_size, process_id)
            elapsed = (time.perf_counter() - start_time) * 1000  # ms
            self._update_performance('Best Fit', elapsed)
            self.performance_metrics['Best Fit']['last_position'] = best_block_idx
            self.log_messages.append(
                f"Best Fit: Allocated P{process_id} ({process_size}KB) to Block {best_block_idx+1} "
                f"(Remaining: {min_diff}KB)"
            )
            return True
        
        self.log_messages.append(
            f"Best Fit: Failed to allocate P{process_id} ({process_size}KB) - no suitable block found"
        )
        return False
    
    def worst_fit(self, process_size, process_id):
        """Worst Fit that finds largest remaining space"""
        start_time = time.perf_counter()
        worst_block_idx = -1
        max_diff = -1
        
        for i, block in enumerate(self.memory_blocks):
            remaining = block['total_size'] - block['allocated_size']
            if remaining >= process_size:
                diff = remaining - process_size
                if diff > max_diff:
                    max_diff = diff
                    worst_block_idx = i
        
        if worst_block_idx != -1:
            self._allocate_block(worst_block_idx, process_size, process_id)
            elapsed = (time.perf_counter() - start_time) * 1000  # ms
            self._update_performance('Worst Fit', elapsed)
            self.performance_metrics['Worst Fit']['last_position'] = worst_block_idx
            self.log_messages.append(
                f"Worst Fit: Allocated P{process_id} ({process_size}KB) to Block {worst_block_idx+1} "
                f"(Remaining: {max_diff}KB)"
            )
            return True
        
        self.log_messages.append(
            f"Worst Fit: Failed to allocate P{process_id} ({process_size}KB) - no suitable block found"
        )
        return False
    
    def _allocate_block(self, block_idx, process_size, process_id):
        """Helper method to allocate a block"""
        block = self.memory_blocks[block_idx]
        
        # Handle multiple processes in same block
        if block['process_id'] is None:
            block['process_id'] = [process_id]
        elif isinstance(block['process_id'], list):
            block['process_id'].append(process_id)
        else:
            block['process_id'] = [block['process_id'], process_id]
            
        block['allocated_size'] += process_size
        block['fragmentation'] = block['total_size'] - block['allocated_size']
        block['status'] = 'Allocated'
        
        self.process_history.append({
            'id': process_id,
            'size': process_size,
            'block_id': block['id'],
            'timestamp': time.time(),
            'algorithm': self.current_algorithm
        })
        self.update_metrics()
    
    def deallocate_process(self, process_id=None):
        """Deallocate a process (last allocated if none specified)"""
        if not process_id and self.process_history:
            process_id = self.process_history[-1]['id']
        
        for block in self.memory_blocks:
            if block['process_id'] and ((isinstance(block['process_id'], list) and process_id in block['process_id']) or block['process_id'] == process_id):
                if isinstance(block['process_id'], list):
                    block['process_id'].remove(process_id)
                    if not block['process_id']:
                        block['process_id'] = None
                        block['status'] = 'Free'
                else:
                    block['process_id'] = None
                    block['status'] = 'Free'
                
                # Find and remove the process from history
                for i, p in enumerate(self.process_history):
                    if p['id'] == process_id:
                        block['allocated_size'] -= p['size']
                        block['fragmentation'] = block['total_size'] - block['allocated_size']
                        self.process_history.pop(i)
                        break
                
                self.update_metrics()
                self.log_messages.append(f"Deallocated process P{process_id} from Block {block['id']}")
                return True
        
        self.log_messages.append(f"Failed to deallocate process P{process_id} - not found")
        return False
    
    def _update_performance(self, algorithm, elapsed_time):
        """Update performance metrics for an algorithm"""
        metrics = self.performance_metrics[algorithm]
        metrics['allocations'] += 1
        metrics['total_time'] += elapsed_time
        metrics['avg_time'] = metrics['total_time'] / metrics['allocations'] if metrics['allocations'] > 0 else 0
    
    def get_performance_data(self):
        """Return formatted performance data"""
        return [
            {
                'Algorithm': algo,
                'Allocations': data['allocations'],
                'Avg Time (ms)': f"{data['avg_time']:.2f}",
                'Total Time (ms)': f"{data['total_time']:.2f}"
            }
            for algo, data in self.performance_metrics.items()
        ]
    
    def generate_load(self, num_processes=10):
        """Generate random processes for testing"""
        sizes = [random.randint(10, self.partition_size-1) for _ in range(num_processes)]
        for i, size in enumerate(sizes):
            pid = f"P{i+1}"
            if not self.allocate(size, pid):
                self.log_messages.append(f"Failed to allocate process {pid} with size {size}KB")

    def allocate(self, process_size, process_id):
        """Allocate using current algorithm"""
        if self.current_algorithm == 'First Fit':
            return self.first_fit(process_size, process_id)
        elif self.current_algorithm == 'Next Fit':
            return self.next_fit(process_size, process_id)
        elif self.current_algorithm == 'Best Fit':
            return self.best_fit(process_size, process_id)
        elif self.current_algorithm == 'Worst Fit':
            return self.worst_fit(process_size, process_id)
        return False

class MemorySimulatorUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Ultimate Memory Allocation Simulator")
        self.allocator = MemoryAllocator()
        
        # Configure dark blue theme
        self.setup_dark_theme()
        
        # Configure main window
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # Create main frames
        self.create_control_panel()
        self.create_performance_panel()
        self.create_memory_view()
        self.create_log_panel()
        
        # Initialize visualization
        self.update_display()
    
    def setup_dark_theme(self):
       
        self.root.configure(bg='#0a1a2a')
        
        # Custom style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Background colors
        self.style.configure('.', background='#0a1a2a', foreground='white')
        self.style.configure('TFrame', background='#0a1a2a')
        self.style.configure('TLabel', background='#0a1a2a', foreground='white')
        self.style.configure('TButton', background='#1a3a5a', foreground='white')
        self.style.configure('TRadiobutton', background='#0a1a2a', foreground='white')
        self.style.configure('TEntry', fieldbackground='#1a3a5a', foreground='white')
        self.style.configure('TScrollbar', background='#1a3a5a')
        self.style.configure('Treeview', background='#1a3a5a', fieldbackground='#1a3a5a', foreground='white')
        self.style.map('Treeview', background=[('selected', '#3a5a7a')])
        
        # Configure matplotlib dark theme
        plt.style.use('dark_background')
        plt.rcParams['axes.facecolor'] = '#0a1a2a'
        plt.rcParams['figure.facecolor'] = '#0a1a2a'
        plt.rcParams['axes.labelcolor'] = 'white'
        plt.rcParams['text.color'] = 'white'
        plt.rcParams['xtick.color'] = 'white'
        plt.rcParams['ytick.color'] = 'white'
    
    def create_control_panel(self):
        """Create the left control panel"""
        self.control_frame = ttk.LabelFrame(self.root, text="Controls", padding=15)
        self.control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Algorithm selection
        ttk.Label(self.control_frame, text="Algorithm:", font=('Helvetica', 10, 'bold')).grid(row=0, column=0, sticky="w", pady=(0,10))
        self.algo_var = tk.StringVar(value="First Fit")
        
        algorithms = ["First Fit", "Next Fit", "Best Fit", "Worst Fit"]
        for i, algo in enumerate(algorithms):
            ttk.Radiobutton(
                self.control_frame, 
                text=algo, 
                variable=self.algo_var, 
                value=algo,
                command=self.update_algorithm,
                style='TRadiobutton'
            ).grid(row=i+1, column=0, sticky="w", pady=2)
        
        # Process controls
        ttk.Label(self.control_frame, text="Process Size (KB):", font=('Helvetica', 10, 'bold')).grid(row=5, column=0, sticky="w", pady=(15,5))
        self.process_size = ttk.Entry(self.control_frame, width=10, style='TEntry')
        self.process_size.grid(row=5, column=1, sticky="w", padx=5)
        self.process_size.insert(0, "50")
        
        ttk.Button(
            self.control_frame, 
            text="Allocate Process", 
            command=self.allocate_process,
            style='TButton'
        ).grid(row=6, column=0, pady=10, sticky="ew", columnspan=2)
        
        ttk.Button(
            self.control_frame, 
            text="Deallocate Process", 
            command=self.deallocate_process,
            style='TButton'
        ).grid(row=7, column=0, pady=5, sticky="ew", columnspan=2)
        
        ttk.Button(
            self.control_frame, 
            text="Reset Memory", 
            command=self.reset_memory,
            style='TButton'
        ).grid(row=8, column=0, pady=10, sticky="ew", columnspan=2)
        
        # Memory configuration
        ttk.Label(self.control_frame, text="Memory Configuration", font=('Helvetica', 10, 'bold')).grid(row=9, column=0, sticky="w", pady=(15,5))
        
        ttk.Label(self.control_frame, text="Memory Size (KB):").grid(row=10, column=0, sticky="w")
        self.mem_size = ttk.Entry(self.control_frame, width=10, style='TEntry')
        self.mem_size.grid(row=10, column=1, sticky="w", padx=5)
        self.mem_size.insert(0, "2048")
        
        ttk.Label(self.control_frame, text="Partition Size (KB):").grid(row=11, column=0, sticky="w")
        self.part_size = ttk.Entry(self.control_frame, width=10, style='TEntry')
        self.part_size.grid(row=11, column=1, sticky="w", padx=5)
        self.part_size.insert(0, "100")
        
        ttk.Button(
            self.control_frame, 
            text="Reconfigure Memory", 
            command=self.reconfigure_memory,
            style='TButton'
        ).grid(row=12, column=0, columnspan=2, pady=10, sticky="ew")
        
        # Test controls
        ttk.Label(self.control_frame, text="Testing", font=('Helvetica', 10, 'bold')).grid(row=13, column=0, sticky="w", pady=(15,5))
        ttk.Button(
            self.control_frame, 
            text="Generate Random Load", 
            command=self.generate_load,
            style='TButton'
        ).grid(row=14, column=0, columnspan=2, pady=5, sticky="ew")
        
        # Algorithm comparison button
        ttk.Button(
            self.control_frame, 
            text="Compare Algorithms", 
            command=self.show_algorithm_comparison,
            style='TButton'
        ).grid(row=15, column=0, columnspan=2, pady=(20,5), sticky="ew")
        
        # Show allocation history button
        ttk.Button(
            self.control_frame, 
            text="Show Allocation History", 
            command=self.show_allocation_history,
            style='TButton'
        ).grid(row=16, column=0, columnspan=2, pady=(5,5), sticky="ew")
    
    def create_performance_panel(self):
        """Create the middle performance panel"""
        self.stats_frame = ttk.LabelFrame(self.root, text="Performance Analytics", padding=15)
        self.stats_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        # Current stats
        self.stats_text = tk.StringVar()
        ttk.Label(
            self.stats_frame, 
            textvariable=self.stats_text, 
            justify="left",
            font=('Helvetica', 9)
        ).grid(row=0, column=0, sticky="nw", pady=(0,15))
        
        # Performance table
        columns = ("Algorithm", "Allocations", "Avg Time (ms)")
        self.performance_tree = ttk.Treeview(
            self.stats_frame, 
            columns=columns, 
            show="headings", 
            height=5,
            style='Treeview'
        )
        
        for col in columns:
            self.performance_tree.heading(col, text=col, anchor='center')
            self.performance_tree.column(col, width=100, anchor='center')
        
        self.performance_tree.grid(row=1, column=0, pady=10, sticky="nsew")
        
        # Memory usage chart
        ttk.Label(self.stats_frame, text="Memory Usage Over Time:", font=('Helvetica', 10, 'bold')).grid(row=2, column=0, sticky="nw", pady=(15,5))
        
        self.fig, self.ax = plt.subplots(figsize=(6, 3))
        self.fig_canvas = FigureCanvasTkAgg(self.fig, master=self.stats_frame)
        self.fig_canvas.get_tk_widget().grid(row=3, column=0, sticky="nsew", pady=(0,15))
        
        # Algorithm comparison chart
        ttk.Label(self.stats_frame, text="Algorithm Comparison:", font=('Helvetica', 10, 'bold')).grid(row=4, column=0, sticky="nw", pady=(5,5))
        
        self.comp_fig, self.comp_ax = plt.subplots(figsize=(6, 3))
        self.comp_canvas = FigureCanvasTkAgg(self.comp_fig, master=self.stats_frame)
        self.comp_canvas.get_tk_widget().grid(row=5, column=0, sticky="nsew")
    
    def create_memory_view(self):
        """Create the right-side memory blocks visualization"""
        self.memory_frame = ttk.LabelFrame(self.root, text="Memory Blocks Visualization", padding=15)
        self.memory_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
        
        # Create canvas and scrollbar
        self.mem_canvas = tk.Canvas(self.memory_frame, bg='#1a3a5a', highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.memory_frame, orient="vertical", command=self.mem_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.mem_canvas)
        
        # Configure scroll region
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.mem_canvas.configure(
                scrollregion=self.mem_canvas.bbox("all")
            )
        )
        
        # Create window in canvas
        self.mem_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.mem_canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack widgets
        self.scrollbar.pack(side="right", fill="y")
        self.mem_canvas.pack(side="left", fill="both", expand=True)
        
        # Create block widgets (will be populated in update)
        self.block_frames = []
    
    def create_log_panel(self):
        """Add a log panel to show allocation messages"""
        self.log_frame = ttk.LabelFrame(self.root, text="Allocation Logs", padding=10)
        self.log_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        
        self.log_text = tk.Text(
            self.log_frame, 
            height=5, 
            bg='#1a3a5a', 
            fg='white',
            state='disabled'
        )
        scrollbar = ttk.Scrollbar(self.log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.log_text.pack(fill="both", expand=True)
    
    def update_algorithm(self):
        """Update the current allocation algorithm"""
        self.allocator.current_algorithm = self.algo_var.get()
        self.update_display()
    
    def allocate_process(self):
        """Allocate a new process"""
        try:
            size = int(self.process_size.get())
            if size <= 0:
                raise ValueError
            
            pid = f"P{len(self.allocator.process_history) + 1}"
            
            if not self.allocator.allocate(size, pid):
                messagebox.showwarning(
                    "Allocation Failed", 
                    f"No suitable block found for {size}KB process!"
                )
            
            self.update_display()
        except ValueError:
            messagebox.showerror(
                "Invalid Input", 
                "Please enter a valid positive integer for process size"
            )
    
    def deallocate_process(self):
        """Deallocate the last process"""
        if not self.allocator.process_history:
            messagebox.showinfo(
                "No Processes", 
                "No processes to deallocate"
            )
            return
        
        self.allocator.deallocate_process()
        self.update_display()
    
    def reset_memory(self):
        """Reset memory to initial state"""
        self.allocator.reset_memory()
        self.update_display()
    
    def reconfigure_memory(self):
        """Change memory configuration"""
        try:
            total = int(self.mem_size.get())
            part = int(self.part_size.get())
            
            if total <= 0 or part <= 0:
                raise ValueError
            if total % part != 0:
                raise ValueError("Total memory must be divisible by partition size")
            
            self.allocator.total_memory = total
            self.allocator.partition_size = part
            self.reset_memory()
        except ValueError as e:
            messagebox.showerror(
                "Invalid Configuration", 
                f"Invalid memory configuration: {str(e)}"
            )
    
    def generate_load(self):
        """Generate random processes for testing"""
        self.allocator.generate_load(10)
        self.update_display()
    
    def show_algorithm_comparison(self):
        """Show comparative performance of all algorithms"""
        self.comp_ax.clear()
        
        algorithms = list(self.allocator.performance_metrics.keys())
        allocations = [data['allocations'] for data in self.allocator.performance_metrics.values()]
        avg_times = [data['avg_time'] for data in self.allocator.performance_metrics.values()]
        
        x = np.arange(len(algorithms))
        width = 0.35
        
        # Plot allocations
        bars1 = self.comp_ax.bar(x - width/2, allocations, width, label='Allocations', color='#4c8bf5')
        # Plot average times
        bars2 = self.comp_ax.bar(x + width/2, avg_times, width, label='Avg Time (ms)', color='#f54c4c')
        
        # Add labels and title
        self.comp_ax.set_xlabel('Algorithm')
        self.comp_ax.set_title('Algorithm Performance Comparison')
        self.comp_ax.set_xticks(x)
        self.comp_ax.set_xticklabels(algorithms)
        self.comp_ax.legend()
        
        # Add value labels
        self.comp_ax.bar_label(bars1, padding=3)
        self.comp_ax.bar_label(bars2, padding=3)
        
        self.comp_canvas.draw()
    
    def show_allocation_history(self):
        """Show a window with the complete allocation history"""
        history_window = tk.Toplevel(self.root)
        history_window.title("Allocation History")
        history_window.geometry("600x400")
        
        # Create a treeview to display the history
        columns = ("Process", "Size", "Block", "Algorithm", "Timestamp")
        tree = ttk.Treeview(
            history_window, 
            columns=columns, 
            show="headings", 
            style='Treeview'
        )
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        # Add data to the treeview
        for process in self.allocator.process_history:
            tree.insert("", "end", values=(
                process['id'],
                f"{process['size']}KB",
                process['block_id'],
                process['algorithm'],
                time.strftime('%H:%M:%S', time.localtime(process['timestamp']))
            ))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(history_window, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)
    
    def update_display(self):
        """Update all visual elements"""
        self.update_memory_blocks()
        self.update_performance_stats()
        self.update_chart()
        self.update_logs()
        self.show_algorithm_comparison()
    
    def update_logs(self):
        """Update the log panel with new messages"""
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        
        for msg in self.allocator.log_messages[-20:]:  # Show last 20 messages
            self.log_text.insert(tk.END, msg + "\n")
        
        self.log_text.config(state='disabled')
        self.log_text.see(tk.END)
    
    def update_memory_blocks(self):
        """Update the memory blocks visualization"""
        # Clear existing widgets
        for widget in self.block_frames:
            widget.destroy()
        self.block_frames = []
        
        # Create new block widgets
        for i, block in enumerate(self.allocator.memory_blocks):
            frame = ttk.Frame(
                self.scrollable_frame, 
                borderwidth=1, 
                relief="solid", 
                padding=10
            )
            frame.grid(row=i, column=0, sticky="ew", pady=5, padx=5)
            
            # Block header
            header = f"Block {block['id']}: {block['total_size']}KB"
            status = " (Allocated)" if block['status'] == 'Allocated' else " (Free)"
            ttk.Label(
                frame, 
                text=header + status, 
                font=('Helvetica', 10, 'bold'),
                foreground='yellow' if block['status'] == 'Allocated' else '#aaffaa'
            ).grid(row=0, column=0, sticky="w", columnspan=2)
            
            # Progress bar - yellow for allocated, black for free
            progress = ttk.Progressbar(
                frame,
                orient="horizontal",
                length=200,
                mode="determinate",
                maximum=block['total_size'],
                style='yellow.Horizontal.TProgressbar' if block['status'] == 'Allocated' else 'black.Horizontal.TProgressbar'
            )
            progress['value'] = block['allocated_size']
            progress.grid(row=1, column=0, sticky="ew", columnspan=2, pady=5)
            
            # Allocation info
            if block['status'] == 'Allocated':
                # Show all processes in this block
                if isinstance(block['process_id'], list):
                    processes = ", ".join([f"P{pid}" for pid in block['process_id']])
                else:
                    processes = f"P{block['process_id']}"
                
                ttk.Label(
                    frame,
                    text=f"Processes: {processes}",
                    foreground='white'
                ).grid(row=2, column=0, sticky="w")
                
                ttk.Label(
                    frame,
                    text=f"Allocated: {block['allocated_size']}KB",
                    foreground='white'
                ).grid(row=3, column=0, sticky="w")
                
                ttk.Label(
                    frame,
                    text=f"Fragmentation: {block['fragmentation']}KB",
                    foreground='#ff6666'
                ).grid(row=4, column=0, sticky="w")
            else:
                ttk.Label(
                    frame,
                    text=f"Free: {block['total_size']}KB",
                    foreground='#aaaaaa',
                    font=('Helvetica', 9, 'bold')
                ).grid(row=2, column=0, sticky="w", columnspan=2)
            
            self.block_frames.append(frame)
        
        # Update scroll region
        self.mem_canvas.configure(scrollregion=self.mem_canvas.bbox("all"))
    
    def update_performance_stats(self):
        """Update the performance statistics display"""
        stats = (
            f"Memory Utilization: {self.allocator.utilization:.2f}%\n"
            f"Allocated: {self.allocator.allocated_memory} KB | Free: {self.allocator.free_memory} KB\n"
            f"Internal Fragmentation: {self.allocator.internal_frag} KB\n"
            f"External Fragmentation: {self.allocator.external_frag} KB\n"
            f"Current Algorithm: {self.allocator.current_algorithm}\n"
            f"Processes Allocated: {len(self.allocator.process_history)}"
        )
        self.stats_text.set(stats)
        
        # Update performance table
        for item in self.performance_tree.get_children():
            self.performance_tree.delete(item)
        
        for algo, data in self.allocator.performance_metrics.items():
            self.performance_tree.insert("", "end", values=(
                algo,
                data['allocations'],
                f"{data['avg_time']:.2f}"
            ))
    
    def update_chart(self):
        """Update the memory usage chart"""
        self.ax.clear()
        
        if len(self.allocator.memory_usage_history) > 1:
            self.ax.plot(
                self.allocator.memory_usage_history, 
                marker='o', 
                linestyle='-', 
                color='#4c8bf5',
                linewidth=2,
                markersize=6
            )
            self.ax.set_title("Memory Utilization Over Time", pad=10)
            self.ax.set_xlabel("Operation Sequence", labelpad=10)
            self.ax.set_ylabel("Utilization (%)", labelpad=10)
            self.ax.set_ylim(0, 100)
            self.ax.grid(True, color='#3a5a7a', linestyle='--', alpha=0.5)
        
        self.fig_canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    # Configure custom progressbar styles
style = ttk.Style()
style.theme_use('clam') 
# Use a theme that supports customization

style.configure('white.Horizontal.TProgressbar', 
                background='#ffffff', 
                troughcolor='#1a3a5a',
                bordercolor='#1a3a5a',
                lightcolor='#ffffff',
                darkcolor='#ffffff')
                
style.configure('yellow.Horizontal.TProgressbar', 
                background='#FFD700',  
                troughcolor='#1a3a5a',
                bordercolor='#1a3a5a',
                lightcolor='#FFD700',
                darkcolor='#FFD700')
                
style.configure('black.Horizontal.TProgressbar', 
                background='#000000',
                troughcolor='#1a3a5a',
                bordercolor='#1a3a5a')
app = MemorySimulatorUI(root)
root.mainloop()

#python memory_visualizer.py
