import pygame
import sys
import random
import time
import math
from enum import Enum
from collections import deque
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from threading import Lock, Semaphore, Thread

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 1600, 900
FPS = 60
BACKGROUND_COLOR = (25, 25, 35)
TEXT_COLOR = (240, 240, 240)
HIGHLIGHT_COLOR = (100, 180, 255)
BUTTON_COLOR = (70, 70, 90)
BUTTON_HOVER_COLOR = (90, 90, 110)
GRID_COLOR = (60, 60, 70)

# Visual Element Sizes
PHILOSOPHER_RADIUS = 60
CHOPSTICK_WIDTH = 10
CHOPSTICK_LENGTH = 120
TABLE_RADIUS = 300
PLATE_RADIUS = 40
CHOPSTICK_ANGLE_OFFSET = math.pi/6  # Angle between chopstick and radius

# Enhanced State Colors
class StateColor:
    THINKING = (70, 130, 255)    # Brighter blue
    HUNGRY = (255, 150, 50)      # Vibrant orange
    EATING = (50, 220, 100)      # Brighter green
    DEADLOCK = (255, 60, 60)     # Bright red
    CHOPSTICK_AVAIL = (230, 180, 50)  # Gold
    CHOPSTICK_TAKEN = (255, 80, 80)   # Red
    CHOPSTICK_HIGHLIGHT = (100, 255, 255)  # Cyan for pickup
    WAITER = (180, 100, 220)     # Purple for waiter lock
    MUTEX = (100, 220, 220)      # Cyan for mutex
    CONNECTION_LINE = (200, 200, 200, 150)  # Semi-transparent
    TABLE_COLOR = (80, 50, 30)
    PLATE_COLOR = (240, 240, 240)
    ARBITRATOR = (220, 180, 60)  # Gold for arbitrator
    PHILOSOPHER_COLOR = (255, 215, 0)  # Gold-like color for philosophers

# States
class PhilosopherState(Enum):
    THINKING = "Thinking"
    HUNGRY = "Hungry"
    EATING = "Eating"
    WAITING = "Waiting"

# Solution Variations with unique features
class SolutionVariation(Enum):
    DEADLOCK_PRONE = "Deadlock-Prone"
    WAITER_LOCK = "Waiter Lock"
    ALTERNATE_PICKUP = "Alternate Pick-Up"
    HIERARCHY_ENFORCED = "Hierarchy Enforced"
    ATOMIC_CHECK = "Atomic Check"
    RESOURCE_ARBITRATION = "Resource Arbitration"

@dataclass
class Chopstick:
    id: int
    owner: Optional[int] = None
    lock: Lock = Lock()
    position: Tuple[float, float] = (0, 0)
    highlight: bool = False
    angle: float = 0.0  # For orientation
    requests: List[int] = None  # For arbitration
    in_hand: bool = False  # Whether the chopstick is in philosopher's hand
    hand_position: Tuple[float, float] = (0, 0)  # Position when in hand

    def __post_init__(self):
        self.requests = []

@dataclass
class Philosopher:
    id: int
    state: PhilosopherState
    position: Tuple[float, float]
    left_chopstick: Optional[Chopstick] = None
    right_chopstick: Optional[Chopstick] = None
    stats: Dict[str, int] = None
    last_state_change: float = 0.0
    progress: float = 0.0
    action_text: str = ""
    action_timer: float = 0.0
    eating_start_time: float = 0.0
    priority: int = 0  # For arbitration
    head_position: Tuple[float, float] = (0, 0)  # Position of the head
    hand_positions: Tuple[Tuple[float, float], Tuple[float, float]] = ((0, 0), (0, 0))  # Left and right hand positions

class PhilosopherLogger:
    def __init__(self, max_lines=10, max_history=100):
        self.logs = {i: deque(maxlen=max_history) for i in range(5)}  # Separate logs for each philosopher
        self.max_lines = max_lines
        self.visible = False  # Start with logs hidden
        self.scroll_positions = {i: 0 for i in range(5)}  # Track scroll position per philosopher
        self.expanded_philosopher = None  # Which philosopher's log is expanded (None means collapsed view)
        
    def add_log(self, philosopher_id, message):
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        colored_message = f"[{timestamp}] {message}"
        self.logs[philosopher_id].append(colored_message)
        
    def get_logs(self, philosopher_id):
        """Get logs for a specific philosopher with scroll position"""
        logs = list(self.logs[philosopher_id])
        start = max(0, len(logs) - self.max_lines - self.scroll_positions[philosopher_id])
        end = start + self.max_lines
        return logs[start:end]
        
    def scroll_up(self, philosopher_id):
        if self.scroll_positions[philosopher_id] < len(self.logs[philosopher_id]) - self.max_lines:
            self.scroll_positions[philosopher_id] += 1
            
    def scroll_down(self, philosopher_id):
        if self.scroll_positions[philosopher_id] > 0:
            self.scroll_positions[philosopher_id] -= 1

class DiningPhilosophersVisualizer:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Dining Philosophers Visualizer - Enhanced")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 20)
        self.title_font = pygame.font.SysFont('Arial', 28, bold=True)
        self.small_font = pygame.font.SysFont('Arial', 16)
        
        # Log system
        self.logger = PhilosopherLogger(max_lines=5, max_history=50)
        self.log_surface = pygame.Surface((400, 300), pygame.SRCALPHA)
        self.last_log_time = 0
        self.log_font = pygame.font.SysFont('Consolas', 14)
        self.log_title_font = pygame.font.SysFont('Consolas', 16, bold=True)
        
        # Load philosopher image (simulated with drawing)
        self.philosopher_img = None
        self._create_philosopher_image()
        
        # Simulation state
        self.philosophers: List[Philosopher] = []
        self.chopsticks: List[Chopstick] = []
        self.variation = SolutionVariation.DEADLOCK_PRONE
        self.is_running = False
        self.simulation_speed = 1.0
        self.show_help = False
        self.show_stats = True
        self.step_mode = False
        self.deadlock_detected = False
        self.waiter = Semaphore(4)  # For waiter lock
        self.global_lock = Lock()   # For atomic check
        self.arbitrator_lock = Lock()  # For resource arbitration
        self.arbitrator_queue = []  # For resource arbitration
        
        # Statistics
        self.simulation_start_time = time.time()
        self.total_meals = 0
        self.deadlock_count = 0
        self.starvation_counts = [0] * 5
        self.last_chopstick_move = 0
        self.performance_stats = {
            'throughput': 0,
            'avg_wait_time': 0,
            'fairness_index': 0
        }
        
        # UI elements
        self._setup_ui()
        self._initialize_simulation()
    
    def _create_philosopher_image(self):
        """Create a simple philosopher image with a face and hands"""
        size = PHILOSOPHER_RADIUS * 2
        self.philosopher_img = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Draw body (simple circle)
        pygame.draw.circle(self.philosopher_img, StateColor.PHILOSOPHER_COLOR, 
                          (size//2, size//2), PHILOSOPHER_RADIUS)
        
        # Draw face features
        pygame.draw.circle(self.philosopher_img, (0, 0, 0), 
                          (size//2 - 15, size//2 - 10), 5)  # Left eye
        pygame.draw.circle(self.philosopher_img, (0, 0, 0), 
                          (size//2 + 15, size//2 - 10), 5)  # Right eye
        pygame.draw.arc(self.philosopher_img, (0, 0, 0),
                       (size//2 - 15, size//2, 30, 20), 
                       3.14, 6.28, 2)  # Smile
    
    def _setup_ui(self):
        """Initialize UI elements with left-side analytics"""
        self.buttons = {
            'start_pause': {'rect': pygame.Rect(50, 50, 180, 50), 'text': "Start", 'color': BUTTON_COLOR},
            'step': {'rect': pygame.Rect(250, 50, 180, 50), 'text': "Step", 'color': BUTTON_COLOR},
            'reset': {'rect': pygame.Rect(450, 50, 180, 50), 'text': "Reset", 'color': BUTTON_COLOR},
            'speed_up': {'rect': pygame.Rect(650, 50, 80, 50), 'text': ">>", 'color': BUTTON_COLOR},
            'slow_down': {'rect': pygame.Rect(750, 50, 80, 50), 'text': "<<", 'color': BUTTON_COLOR},
            'deadlock_prone': {'rect': pygame.Rect(50, 120, 200, 50), 'text': "Deadlock", 'color': (150, 80, 80)},
            'waiter_lock': {'rect': pygame.Rect(260, 120, 200, 50), 'text': "Waiter", 'color': (180, 100, 220)},
            'alternate_pickup': {'rect': pygame.Rect(470, 120, 200, 50), 'text': "Alternate", 'color': (80, 150, 80)},
            'hierarchy': {'rect': pygame.Rect(50, 190, 200, 50), 'text': "Hierarchy", 'color': (80, 80, 150)},
            'atomic_check': {'rect': pygame.Rect(260, 190, 200, 50), 'text': "Atomic", 'color': (100, 180, 180)},
            'arbitration': {'rect': pygame.Rect(470, 190, 200, 50), 'text': "Arbitration", 'color': (220, 180, 60)},
            'show_stats': {'rect': pygame.Rect(680, 50, 200, 50), 'text': "Toggle Stats", 'color': BUTTON_COLOR},
            'help': {'rect': pygame.Rect(680, 120, 200, 50), 'text': "Help", 'color': BUTTON_COLOR},
            'show_logs': {'rect': pygame.Rect(680, 190, 200, 50), 'text': "Toggle Logs", 'color': BUTTON_COLOR},
        }
    
    def _initialize_simulation(self):
        """Set up philosophers and chopsticks in a circular arrangement on right side"""
        self.philosophers = []
        self.chopsticks = []
        self.deadlock_detected = False
        self.total_meals = 0
        self.deadlock_count = 0
        self.simulation_start_time = time.time()
        self.arbitrator_queue = []
        
        # Right-side table position
        center_x, center_y = SCREEN_WIDTH - 400, SCREEN_HEIGHT // 2
        radius = TABLE_RADIUS
        num_philosophers = 5
        
        # Create chopsticks (positioned between philosophers)
        for i in range(num_philosophers):
            angle = 2 * math.pi * i / num_philosophers
            # Position chopsticks slightly inward from the midpoint between philosophers
            x = center_x + 0.85 * radius * math.sin(angle)
            y = center_y - 0.85 * radius * math.cos(angle)
            chopstick_angle = angle + CHOPSTICK_ANGLE_OFFSET  # Angled for better visibility
            self.chopsticks.append(Chopstick(id=i, position=(x, y), angle=chopstick_angle))
        
        # Create philosophers
        for i in range(num_philosophers):
            angle = 2 * math.pi * i / num_philosophers
            x = center_x + radius * math.sin(angle)
            y = center_y - radius * math.cos(angle)
            
            left_chop = self.chopsticks[i]
            right_chop = self.chopsticks[(i + 1) % num_philosophers]
            
            # Calculate hand positions (slightly offset from body)
            hand_distance = PHILOSOPHER_RADIUS * 0.7
            left_hand_pos = (x - hand_distance * math.cos(angle - math.pi/4),
                            y - hand_distance * math.sin(angle - math.pi/4))
            right_hand_pos = (x + hand_distance * math.cos(angle - math.pi/4),
                             y + hand_distance * math.sin(angle - math.pi/4))
            
            self.philosophers.append(Philosopher(
                id=i,
                state=PhilosopherState.THINKING,
                position=(x, y),
                left_chopstick=left_chop,
                right_chopstick=right_chop,
                stats={
                    'meals': 0,
                    'thinking_time': 0,
                    'waiting_time': 0,
                    'eating_time': 0,
                    'starvation_count': 0
                },
                last_state_change=time.time(),
                priority=random.randint(1, 10),  # Random initial priority
                head_position=(x, y - PHILOSOPHER_RADIUS//2),
                hand_positions=(left_hand_pos, right_hand_pos)
            ))
    
    def _draw_chopstick(self, chopstick):
        """Draw a chopstick with clear ownership indication and animation"""
        if chopstick.in_hand:
            # Draw chopstick in philosopher's hand
            x, y = chopstick.hand_position
            end_x1 = x - (CHOPSTICK_LENGTH//2) * math.cos(chopstick.angle)
            end_y1 = y - (CHOPSTICK_LENGTH//2) * math.sin(chopstick.angle)
            end_x2 = x + (CHOPSTICK_LENGTH//2) * math.cos(chopstick.angle)
            end_y2 = y + (CHOPSTICK_LENGTH//2) * math.sin(chopstick.angle)
        else:
            # Draw chopstick on table
            x, y = chopstick.position
            end_x1 = x - (CHOPSTICK_LENGTH//2) * math.cos(chopstick.angle)
            end_y1 = y - (CHOPSTICK_LENGTH//2) * math.sin(chopstick.angle)
            end_x2 = x + (CHOPSTICK_LENGTH//2) * math.cos(chopstick.angle)
            end_y2 = y + (CHOPSTICK_LENGTH//2) * math.sin(chopstick.angle)
        
        # Choose color based on state
        if chopstick.highlight:
            color = StateColor.CHOPSTICK_HIGHLIGHT
            chopstick.highlight = False  # Reset highlight after drawing
        elif chopstick.owner is not None:
            color = StateColor.CHOPSTICK_TAKEN
        else:
            color = StateColor.CHOPSTICK_AVAIL
        
        # Draw thicker chopstick with rounded ends
        pygame.draw.line(self.screen, color, (end_x1, end_y1), (end_x2, end_y2), CHOPSTICK_WIDTH)
        pygame.draw.circle(self.screen, color, (int(end_x1), int(end_y1)), CHOPSTICK_WIDTH//2)
        pygame.draw.circle(self.screen, color, (int(end_x2), int(end_y2)), CHOPSTICK_WIDTH//2)
        
        # Draw owner connection if taken
        if chopstick.owner is not None and not chopstick.in_hand:
            philosopher = next(p for p in self.philosophers if p.id == chopstick.owner)
            px, py = philosopher.position
            
            # Draw a faint connecting line
            line_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.line(line_surface, StateColor.CONNECTION_LINE, 
                            (x, y), (px, py), 2)
            self.screen.blit(line_surface, (0, 0))
            
            # Draw owner indicator near philosopher
            owner_text = self.small_font.render(f"← Chop {chopstick.id}", True, HIGHLIGHT_COLOR)
            text_x = px + (20 if x > px else -20 - owner_text.get_width())
            text_y = py - 30
            self.screen.blit(owner_text, (text_x, text_y))
        
        # For arbitration, show request queue
        if self.variation == SolutionVariation.RESOURCE_ARBITRATION and chopstick.requests:
            queue_text = self.small_font.render(f"Q: {len(chopstick.requests)}", True, (255, 255, 255))
            self.screen.blit(queue_text, (x - 10, y - 20))
    
    def _draw_philosopher(self, philosopher):
        """Draw a philosopher with enhanced state visualization and hands"""
        x, y = philosopher.position
        
        # Draw state circle with border
        border_color = (80, 80, 80)
        pygame.draw.circle(self.screen, border_color, (int(x), int(y)), PHILOSOPHER_RADIUS + 5)
        
        # Draw philosopher body (using our created image)
        body_rect = self.philosopher_img.get_rect(center=(int(x), int(y)))
        self.screen.blit(self.philosopher_img, body_rect)
        
        # Overlay state color with transparency
        overlay = pygame.Surface((PHILOSOPHER_RADIUS*2, PHILOSOPHER_RADIUS*2), pygame.SRCALPHA)
        pygame.draw.circle(overlay, (*self._get_state_color(philosopher.state), 150), 
                          (PHILOSOPHER_RADIUS, PHILOSOPHER_RADIUS), PHILOSOPHER_RADIUS)
        self.screen.blit(overlay, (x - PHILOSOPHER_RADIUS, y - PHILOSOPHER_RADIUS))
        
        # Draw hands (only visible when holding chopsticks)
        left_hand_pos, right_hand_pos = philosopher.hand_positions
        
        # Draw left hand if holding left chopstick
        if philosopher.left_chopstick.owner == philosopher.id and philosopher.left_chopstick.in_hand:
            pygame.draw.circle(self.screen, StateColor.PHILOSOPHER_COLOR, 
                             (int(left_hand_pos[0]), int(left_hand_pos[1])), 15)
        
        # Draw right hand if holding right chopstick
        if philosopher.right_chopstick.owner == philosopher.id and philosopher.right_chopstick.in_hand:
            pygame.draw.circle(self.screen, StateColor.PHILOSOPHER_COLOR, 
                             (int(right_hand_pos[0]), int(right_hand_pos[1])), 15)
        
        # Draw philosopher ID
        id_text = self.font.render(str(philosopher.id), True, (0, 0, 0))
        self.screen.blit(id_text, (int(x) - id_text.get_width()//2, int(y) - id_text.get_height()//2))
        
        # Draw state text with background for readability
        state_text = self.small_font.render(philosopher.state.value, True, TEXT_COLOR)
        text_bg = pygame.Rect(x - state_text.get_width()//2 - 5, 
                             y + PHILOSOPHER_RADIUS + 5,
                             state_text.get_width() + 10,
                             state_text.get_height() + 5)
        pygame.draw.rect(self.screen, (40, 40, 50), text_bg, border_radius=3)
        pygame.draw.rect(self.screen, (80, 80, 80), text_bg, 2, border_radius=3)
        self.screen.blit(state_text, 
                        (int(x) - state_text.get_width()//2, 
                         int(y) + PHILOSOPHER_RADIUS + 8))
        
        # Draw current action if any
        if philosopher.action_text and philosopher.action_timer > time.time():
            action_text = self.small_font.render(philosopher.action_text, True, HIGHLIGHT_COLOR)
            action_bg = pygame.Rect(x - action_text.get_width()//2 - 5,
                                  y + PHILOSOPHER_RADIUS + 35,
                                  action_text.get_width() + 10,
                                  action_text.get_height() + 5)
            pygame.draw.rect(self.screen, (40, 40, 50), action_bg, border_radius=3)
            self.screen.blit(action_text,
                            (int(x) - action_text.get_width()//2,
                             int(y) + PHILOSOPHER_RADIUS + 38))
        
        # Draw animated progress indicator
        if philosopher.state != PhilosopherState.THINKING:
            progress = min(1.0, philosopher.progress)
            start_angle = -math.pi / 2
            end_angle = start_angle + 2 * math.pi * progress
            
            # Smooth animation using easing
            eased_progress = 1 - (1 - progress) ** 2
            end_angle = start_angle + 2 * math.pi * eased_progress
            
            pygame.draw.arc(self.screen, (255, 255, 255),
                          (x - PHILOSOPHER_RADIUS - 10, y - PHILOSOPHER_RADIUS - 10,
                           (PHILOSOPHER_RADIUS + 10) * 2, (PHILOSOPHER_RADIUS + 10) * 2),
                          start_angle, end_angle, 4)
        
        # For arbitration, show priority
        if self.variation == SolutionVariation.RESOURCE_ARBITRATION:
            priority_text = self.small_font.render(f"P:{philosopher.priority}", True, (255, 255, 255))
            self.screen.blit(priority_text, (x - 15, y - 25))
    
    def _draw_table(self):
        """Draw the dining table on the right side"""
        center_x, center_y = SCREEN_WIDTH - 400, SCREEN_HEIGHT // 2
        
        # Draw table with gradient effect
        for r in range(TABLE_RADIUS, TABLE_RADIUS - 40, -5):
            shade = 80 - (TABLE_RADIUS - r) // 2
            pygame.draw.circle(self.screen, (shade, shade - 20, shade - 40),
                              (center_x, center_y), r)
        
        # Draw plates with shadow effect
        for i, philosopher in enumerate(self.philosophers):
            angle = 2 * math.pi * i / len(self.philosophers)
            plate_x = center_x + 0.5 * TABLE_RADIUS * math.sin(angle)
            plate_y = center_y - 0.5 * TABLE_RADIUS * math.cos(angle)
            
            # Plate shadow
            pygame.draw.circle(self.screen, (30, 30, 30),
                              (int(plate_x) + 5, int(plate_y) + 5), PLATE_RADIUS)
            # Plate main
            pygame.draw.circle(self.screen, StateColor.PLATE_COLOR,
                              (int(plate_x), int(plate_y)), PLATE_RADIUS)
            # Plate rim
            pygame.draw.circle(self.screen, (200, 200, 200),
                              (int(plate_x), int(plate_y)), PLATE_RADIUS - 5, 2)
    
    def _draw_sync_primitives(self):
        """Draw visualization of synchronization primitives on left side"""
        primitives_x = 50
        primitives_y = 300
        
        if self.variation == SolutionVariation.WAITER_LOCK:
            # Draw waiter semaphore
            pygame.draw.rect(self.screen, StateColor.WAITER, (primitives_x, primitives_y, 150, 70), border_radius=5)
            pygame.draw.rect(self.screen, (100, 50, 120), (primitives_x, primitives_y, 150, 70), 2, border_radius=5)
            waiter_text = self.font.render(f"Waiter: {self.waiter._value}/4", True, (0, 0, 0))
            self.screen.blit(waiter_text, (primitives_x + 10, primitives_y + 15))
            
            # Additional waiter-specific info
            waiting = sum(1 for p in self.philosophers if p.state == PhilosopherState.HUNGRY and p.action_text == "Waiting for seat...")
            waiting_text = self.small_font.render(f"Waiting: {waiting}", True, (0, 0, 0))
            self.screen.blit(waiting_text, (primitives_x + 10, primitives_y + 40))
            
        elif self.variation == SolutionVariation.ATOMIC_CHECK:
            # Draw mutex lock
            color = StateColor.MUTEX if not self.global_lock.locked() else StateColor.CHOPSTICK_TAKEN
            pygame.draw.rect(self.screen, color, (primitives_x, primitives_y, 150, 70), border_radius=5)
            pygame.draw.rect(self.screen, (50, 100, 100), (primitives_x, primitives_y, 150, 70), 2, border_radius=5)
            mutex_text = self.font.render("Global Lock", True, (0, 0, 0))
            self.screen.blit(mutex_text, (primitives_x + 10, primitives_y + 15))
            status = "Locked" if self.global_lock.locked() else "Unlocked"
            status_text = self.small_font.render(status, True, (0, 0, 0))
            self.screen.blit(status_text, (primitives_x + 10, primitives_y + 40))
            
            # Additional atomic check info
            attempts = sum(p.stats['waiting_time'] for p in self.philosophers)
            attempts_text = self.small_font.render(f"Attempts: {attempts}", True, (0, 0, 0))
            self.screen.blit(attempts_text, (primitives_x + 10, primitives_y + 55))
        
        elif self.variation == SolutionVariation.RESOURCE_ARBITRATION:
            # Draw arbitrator
            pygame.draw.rect(self.screen, StateColor.ARBITRATOR, (primitives_x, primitives_y, 200, 100), border_radius=5)
            pygame.draw.rect(self.screen, (150, 120, 30), (primitives_x, primitives_y, 200, 100), 2, border_radius=5)
            arb_text = self.font.render("Resource Arbitrator", True, (0, 0, 0))
            self.screen.blit(arb_text, (primitives_x + 10, primitives_y + 15))
            
            # Show arbitration queue
            queue_text = self.small_font.render(f"Queue: {len(self.arbitrator_queue)}", True, (0, 0, 0))
            self.screen.blit(queue_text, (primitives_x + 10, primitives_y + 40))
            
            # Show current decision
            if self.arbitrator_queue:
                decision_text = self.small_font.render(f"Next: Phil {self.arbitrator_queue[0]}", True, (0, 0, 0))
                self.screen.blit(decision_text, (primitives_x + 10, primitives_y + 60))
            
            # Show fairness metric
            fairness = self._calculate_fairness()
            fairness_text = self.small_font.render(f"Fairness: {fairness:.2f}", True, (0, 0, 0))
            self.screen.blit(fairness_text, (primitives_x + 10, primitives_y + 80))
    
    def _draw_variation_info(self):
        """Draw information about the current variation on left side"""
        info_rect = pygame.Rect(50, 420, 400, 250)
        pygame.draw.rect(self.screen, (50, 50, 60), info_rect, border_radius=5)
        pygame.draw.rect(self.screen, HIGHLIGHT_COLOR, info_rect, 2, border_radius=5)
        
        # Title
        title = self.font.render(f"{self.variation.value} Mode", True, HIGHLIGHT_COLOR)
        self.screen.blit(title, (info_rect.x + 10, info_rect.y + 10))
        
        # Description with variation-specific details
        descriptions = {
            SolutionVariation.DEADLOCK_PRONE: [
                "• Classic deadlock scenario",
                "• All pick left then right",
                "• Deadlock when all hold one",
                "• No synchronization",
                "",
                "Deadlocks: " + str(self.deadlock_count)
            ],
            SolutionVariation.WAITER_LOCK: [
                "• Limits concurrent access",
                "• Only 4 can sit at table",
                "• Uses a counting semaphore",
                "• Prevents circular wait",
                "",
                "Current seats: " + str(4 - self.waiter._value)
            ],
            SolutionVariation.ALTERNATE_PICKUP: [
                "• Breaks symmetry",
                "• Even IDs: left then right",
                "• Odd IDs: right then left",
                "• Prevents circular wait",
                "",
                "Current pattern:",
                "Even: left→right",
                "Odd: right→left"
            ],
            SolutionVariation.HIERARCHY_ENFORCED: [
                "• Total resource ordering",
                "• Always pick lower-ID first",
                "• Prevents circular wait",
                "• May cause starvation",
                "",
                "Current picking order:",
                "Lower-numbered first"
            ],
            SolutionVariation.ATOMIC_CHECK: [
                "• All-or-nothing approach",
                "• Checks both chopsticks",
                "• Uses global mutex",
                "• May reduce throughput",
                "",
                "Lock status:",
                "Locked" if self.global_lock.locked() else "Unlocked"
            ],
            SolutionVariation.RESOURCE_ARBITRATION: [
                "• Centralized control",
                "• Arbitrator decides access",
                "• Can enforce fairness",
                "• Priority-based",
                "",
                "Current queue:",
                f"{len(self.arbitrator_queue)} waiting",
                f"Next: {self.arbitrator_queue[0] if self.arbitrator_queue else 'None'}"
            ]
        }
        
        y_pos = info_rect.y + 40
        for line in descriptions.get(self.variation, []):
            text = self.small_font.render(line, True, TEXT_COLOR)
            self.screen.blit(text, (info_rect.x + 20, y_pos))
            y_pos += 25
    
    def _draw_stats(self):
        """Draw comprehensive statistics panel on left side"""
        if not self.show_stats:
            return
            
        panel_rect = pygame.Rect(50, 700, 400, 180)
        pygame.draw.rect(self.screen, (50, 50, 60), panel_rect, border_radius=5)
        pygame.draw.rect(self.screen, HIGHLIGHT_COLOR, panel_rect, 2, border_radius=5)
        
        # Title
        title = self.font.render("Performance Metrics", True, TEXT_COLOR)
        self.screen.blit(title, (panel_rect.x + 10, panel_rect.y + 10))
        
        # Calculate metrics
        runtime = time.time() - self.simulation_start_time
        throughput = self.total_meals / max(1, runtime)
        avg_wait = sum(p.stats['waiting_time'] for p in self.philosophers) / max(1, self.total_meals)
        fairness = self._calculate_fairness()
        
        # General stats
        general_stats = [
            f"Runtime: {runtime:.1f}s",
            f"Total meals: {self.total_meals}",
            f"Throughput: {throughput:.2f} meals/s",
            f"Avg wait: {avg_wait:.1f}s",
            f"Fairness: {fairness:.2f}",
            f"Deadlocks: {self.deadlock_count}"
        ]
        
        y_pos = panel_rect.y + 40
        for stat in general_stats:
            text = self.font.render(stat, True, TEXT_COLOR)
            self.screen.blit(text, (panel_rect.x + 20, y_pos))
            y_pos += 25
    
    def _draw_logs(self):
        """Draw the philosopher logs panel as a popup when toggled"""
        if not self.logger.visible:
            return
            
        # Draw the logs panel as a centered popup
        log_width, log_height = 1000, 600
        log_rect = pygame.Rect((SCREEN_WIDTH - log_width) // 2, (SCREEN_HEIGHT - log_height) // 2, log_width, log_height)
        
        # Main panel
        pygame.draw.rect(self.screen, (40, 40, 50), log_rect, border_radius=10)
        pygame.draw.rect(self.screen, HIGHLIGHT_COLOR, log_rect, 2, border_radius=10)
        
        # Close button
        close_rect = pygame.Rect(log_rect.right - 40, log_rect.y + 10, 30, 30)
        pygame.draw.rect(self.screen, (255, 80, 80), close_rect, border_radius=5)
        close_text = self.font.render("X", True, TEXT_COLOR)
        self.screen.blit(close_text, (close_rect.x + 10, close_rect.y + 5))
        
        # Handle close button click
        mouse_pos = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0] and close_rect.collidepoint(mouse_pos):
            self.logger.visible = False
            return
            
        # Title
        title = self.title_font.render("Philosopher Activity Logs", True, HIGHLIGHT_COLOR)
        self.screen.blit(title, (log_rect.x + 20, log_rect.y + 15))
        
        # Draw philosopher tabs
        tab_width = log_width // len(self.philosophers)
        tab_height = 40
        tab_y = log_rect.y + 50
        
        for i, philosopher in enumerate(self.philosophers):
            tab_rect = pygame.Rect(log_rect.x + i * tab_width, tab_y, tab_width, tab_height)
            tab_color = self._get_state_color(philosopher.state) if self.logger.expanded_philosopher != i else HIGHLIGHT_COLOR
            
            pygame.draw.rect(self.screen, tab_color, tab_rect, border_radius=5)
            pygame.draw.rect(self.screen, (80, 80, 80), tab_rect, 2, border_radius=5)
            
            tab_text = self.font.render(f"Phil {i}", True, (0, 0, 0))
            self.screen.blit(tab_text, (tab_rect.centerx - tab_text.get_width() // 2, 
                                      tab_rect.centery - tab_text.get_height() // 2))
            
            # Handle tab click
            if pygame.mouse.get_pressed()[0] and tab_rect.collidepoint(mouse_pos):
                self.logger.expanded_philosopher = i if self.logger.expanded_philosopher != i else None
        
        # Content area
        content_rect = pygame.Rect(log_rect.x + 20, tab_y + tab_height + 20, 
                                 log_width - 40, log_height - tab_height - 80)
        pygame.draw.rect(self.screen, (30, 30, 40), content_rect)
        pygame.draw.rect(self.screen, (60, 60, 70), content_rect, 2)
        
        # Draw logs for the selected philosopher or all if none selected
        if self.logger.expanded_philosopher is not None:
            self._draw_single_philosopher_log(content_rect, self.logger.expanded_philosopher)
        else:
            self._draw_all_philosopher_logs(content_rect)
    
    def _draw_single_philosopher_log(self, content_rect, phil_id):
        """Draw expanded log view for a single philosopher"""
        logs = list(self.logger.logs[phil_id])
        philosopher = self.philosophers[phil_id]
        
        # Header
        header = self.font.render(
            f"Philosopher {phil_id} - {philosopher.state.value} (Priority: {philosopher.priority})", 
            True, 
            self._get_state_color(philosopher.state)
        )
        self.screen.blit(header, (content_rect.x + 10, content_rect.y + 10))
        
        # Scroll buttons
        up_rect = pygame.Rect(content_rect.right - 40, content_rect.y + 10, 30, 30)
        down_rect = pygame.Rect(content_rect.right - 40, content_rect.y + 50, 30, 30)
        
        pygame.draw.rect(self.screen, (80, 80, 100), up_rect, border_radius=5)
        pygame.draw.rect(self.screen, (80, 80, 100), down_rect, border_radius=5)
        
        up_text = self.font.render("↑", True, TEXT_COLOR)
        down_text = self.font.render("↓", True, TEXT_COLOR)
        self.screen.blit(up_text, (up_rect.x + 10, up_rect.y + 5))
        self.screen.blit(down_text, (down_rect.x + 10, down_rect.y + 5))
        
        # Handle scroll button clicks
        mouse_pos = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0]:
            if up_rect.collidepoint(mouse_pos):
                self.logger.scroll_up(phil_id)
            elif down_rect.collidepoint(mouse_pos):
                self.logger.scroll_down(phil_id)
        
        # Log entries
        y_pos = content_rect.y + 50
        visible_lines = (content_rect.height - 60) // 20  # Calculate how many lines fit
        
        logs = self.logger.get_logs(phil_id)
        for log in reversed(logs[-visible_lines:]):  # Show most recent entries that fit
            # Split timestamp from message
            if ']' in log:
                timestamp, message = log.split(']', 1)
                timestamp += ']'
            else:
                timestamp = ''
                message = log
                
            # Render timestamp
            time_surface = self.log_font.render(timestamp, True, (150, 150, 150))
            self.screen.blit(time_surface, (content_rect.x + 10, y_pos))
            
            # Render message
            msg_surface = self.log_font.render(message.strip(), True, TEXT_COLOR)
            self.screen.blit(msg_surface, (content_rect.x + 200, y_pos))
            
            y_pos += 20
            if y_pos > content_rect.bottom - 20:
                break
    
    def _draw_all_philosopher_logs(self, content_rect):
        """Draw condensed log view for all philosophers"""
        columns = 2
        rows = (len(self.philosophers)) // columns
        cell_width = content_rect.width // columns
        cell_height = content_rect.height // rows
        
        for i, philosopher in enumerate(self.philosophers):
            col = i % columns
            row = i // columns
            
            cell_rect = pygame.Rect(
                content_rect.x + col * cell_width,
                content_rect.y + row * cell_height,
                cell_width - 10,
                cell_height - 10
            )
            
            # Cell background
            pygame.draw.rect(self.screen, (50, 50, 60), cell_rect, border_radius=5)
            pygame.draw.rect(self.screen, (80, 80, 80), cell_rect, 2, border_radius=5)
            
            # Philosopher header
            header_color = self._get_state_color(philosopher.state)
            header = self.font.render(f"Philosopher {i}", True, header_color)
            self.screen.blit(header, (cell_rect.x + 10, cell_rect.y + 10))
            
            # Get most recent logs
            logs = self.logger.get_logs(i)
            y_pos = cell_rect.y + 40
            
            for log in reversed(logs[:3]):  # Show 3 most recent logs
                # Clean up timestamp for display
                log_text = log.split(']', 1)[1].strip() if ']' in log else log
                
                # Ensure text fits in cell
                if len(log_text) > 40:
                    log_text = log_text[:37] + "..."
                
                log_display = self.small_font.render(log_text, True, TEXT_COLOR)
                self.screen.blit(log_display, (cell_rect.x + 10, y_pos))
                y_pos += 20
                
                if y_pos > cell_rect.bottom - 20:
                    break
    
    def _calculate_fairness(self):
        """Calculate Jain's fairness index for meal distribution"""
        if not self.philosophers or self.total_meals == 0:
            return 1.0
        
        meals = [p.stats['meals'] for p in self.philosophers]
        sum_sq = sum(m**2 for m in meals)
        sum_total = sum(meals)
        
        if sum_sq == 0:
            return 1.0
            
        return (sum_total ** 2) / (len(meals) * sum_sq)
    
    def _draw_buttons(self):
        """Draw all UI buttons on left side"""
        mouse_pos = pygame.mouse.get_pos()
        
        for name, button in self.buttons.items():
            # Highlight current variation button
            if name == self.variation.name.lower().replace("-", "_"):
                color = HIGHLIGHT_COLOR
            else:
                color = button.get('color', BUTTON_HOVER_COLOR if button['rect'].collidepoint(mouse_pos) else BUTTON_COLOR)
            
            pygame.draw.rect(self.screen, color, button['rect'], border_radius=5)
            pygame.draw.rect(self.screen, GRID_COLOR, button['rect'], 2, border_radius=5)
            
            text = self.font.render(button['text'], True, TEXT_COLOR)
            text_rect = text.get_rect(center=button['rect'].center)
            self.screen.blit(text, text_rect)
        
        # Draw speed indicator
        speed_text = self.font.render(f"Speed: {self.simulation_speed:.1f}x", True, TEXT_COLOR)
        self.screen.blit(speed_text, (890, 70))
    
    def _draw_help(self):
        """Draw the help overlay"""
        if not self.show_help:
            return
            
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        # Help box
        help_rect = pygame.Rect(200, 100, 1200, 700)
        pygame.draw.rect(self.screen, (60, 60, 80), help_rect, border_radius=10)
        pygame.draw.rect(self.screen, HIGHLIGHT_COLOR, help_rect, 2, border_radius=10)
        
        # Title
        title = self.title_font.render("Dining Philosophers Visualizer - Help", True, TEXT_COLOR)
        self.screen.blit(title, (help_rect.x + 20, help_rect.y + 20))
        
        # Content with variation-specific help
        help_text = [
            "This visualizer demonstrates the classic Dining Philosophers problem and various solutions.",
            "Five philosophers sit at a round table with chopsticks between them. Each needs two",
            "chopsticks to eat, leading to potential deadlocks if not properly synchronized.",
            "",
            "Key Features:",
            "• Real-time visualization of philosopher states (Thinking, Hungry, Eating)",
            "• Multiple deadlock prevention algorithms with unique implementations",
            "• Detailed statistics and performance metrics",
            "• Interactive controls and step-by-step execution",
            "",
            "Color Coding:",
            "• Thinking: Blue    Hungry: Orange    Eating: Green    Deadlock: Red",
            "• Available Chopsticks: Gold    Taken Chopsticks: Red",
            "• Waiter Lock: Purple    Global Mutex: Cyan    Arbitrator: Gold",
            "",
            "Unique Variation Features:",
            "• Deadlock-Prone: Classic problem showing circular wait",
            "• Waiter Lock: Limits concurrent access with semaphore",
            "• Alternate Pick-Up: Different order for odd/even IDs",
            "• Hierarchy: Always picks lower-numbered chopstick first",
            "• Atomic Check: Uses global lock for all-or-nothing approach",
            "• Resource Arbitration: Centralized control with priority queue",
            "",
            "Controls:",
            "• Start/Pause: Space    Step: Right Arrow    Help: H",
            "• Reset: Restart simulation    Speed: Adjust simulation speed",
            "• Variations: Select different solutions    Toggle Stats: Show/hide metrics",
            "",
            "Press any key or click outside this box to close help."
        ]
        
        text_y = help_rect.y + 70
        for line in help_text:
            text = self.font.render(line, True, TEXT_COLOR)
            self.screen.blit(text, (help_rect.x + 20, text_y))
            text_y += 30
    
    def _get_state_color(self, state):
        """Get color for philosopher state"""
        if self.deadlock_detected:
            return StateColor.DEADLOCK
        return {
            PhilosopherState.THINKING: StateColor.THINKING,
            PhilosopherState.HUNGRY: StateColor.HUNGRY,
            PhilosopherState.EATING: StateColor.EATING,
            PhilosopherState.WAITING: (200, 200, 200)
        }.get(state, (100, 100, 100))
    
    def _set_action_text(self, philosopher, text, duration=2.0):
        """Set temporary action text for a philosopher"""
        philosopher.action_text = text
        philosopher.action_timer = time.time() + duration
    
    def _log_event(self, philosopher_id, message):
        """Add an event to the log system"""
        self.logger.add_log(philosopher_id, message)
    
    def _update_philosophers(self):
        """Update all philosophers' states"""
        if not self.is_running and not self.step_mode:
            return
            
        self.step_mode = False
        self.deadlock_detected = False
        
        # Check for deadlock (all philosophers holding one chopstick)
        if all(p.state == PhilosopherState.HUNGRY and 
               ((p.left_chopstick.owner == p.id) ^ (p.right_chopstick.owner == p.id))
               for p in self.philosophers):
            self.deadlock_detected = True
            self.deadlock_count += 1
            for p in self.philosophers:
                self._set_action_text(p, "Deadlocked!", 3.0)
                self._log_event(p.id, "Deadlock detected! All philosophers holding one chopstick")
            return
        
        for philosopher in self.philosophers:
            current_time = time.time()
            state_duration = current_time - philosopher.last_state_change
            
            # Update progress for animation
            if philosopher.state == PhilosopherState.THINKING:
                philosopher.progress = state_duration / 3.0  # Think for ~3 seconds
            elif philosopher.state == PhilosopherState.HUNGRY:
                philosopher.progress = state_duration / 5.0  # Wait for ~5 seconds
            else:  # EATING
                philosopher.progress = state_duration / 4.0  # Eat for ~4 seconds
            
            # State transitions
            if philosopher.state == PhilosopherState.THINKING and philosopher.progress >= 1.0:
                self._become_hungry(philosopher)
            elif philosopher.state == PhilosopherState.HUNGRY:
                self._try_eat(philosopher)
            elif philosopher.state == PhilosopherState.EATING and philosopher.progress >= 1.0:
                self._finish_eating(philosopher)
    
    def _become_hungry(self, philosopher):
        """Transition from THINKING to HUNGRY"""
        philosopher.state = PhilosopherState.HUNGRY
        philosopher.last_state_change = time.time()
        philosopher.progress = 0.0
        philosopher.stats['thinking_time'] += 1
        self._set_action_text(philosopher, "Getting hungry...")
        self._log_event(philosopher.id, f"Became hungry after thinking for {philosopher.progress:.1f}s")
        
        # For arbitration, add to chopstick request queues
        if self.variation == SolutionVariation.RESOURCE_ARBITRATION:
            philosopher.left_chopstick.requests.append(philosopher.id)
            philosopher.right_chopstick.requests.append(philosopher.id)
            # Sort requests by priority (higher first)
            philosopher.left_chopstick.requests.sort(key=lambda pid: -self.philosophers[pid].priority)
            philosopher.right_chopstick.requests.sort(key=lambda pid: -self.philosophers[pid].priority)
    
    def _try_eat(self, philosopher):
        """Attempt to acquire chopsticks and start eating"""
        if self._acquire_chopsticks(philosopher):
            philosopher.state = PhilosopherState.EATING
            philosopher.last_state_change = time.time()
            philosopher.progress = 0.0
            philosopher.stats['meals'] += 1
            philosopher.stats['waiting_time'] += 1
            philosopher.eating_start_time = time.time()
            self.total_meals += 1
            self._set_action_text(philosopher, "Started eating!")
            self._log_event(philosopher.id, "Acquired both chopsticks and started eating")
            
            # For arbitration, remove from queues
            if self.variation == SolutionVariation.RESOURCE_ARBITRATION:
                if philosopher.id in philosopher.left_chopstick.requests:
                    philosopher.left_chopstick.requests.remove(philosopher.id)
                if philosopher.id in philosopher.right_chopstick.requests:
                    philosopher.right_chopstick.requests.remove(philosopher.id)
        else:
            # Check for starvation (waiting too long)
            wait_time = time.time() - philosopher.last_state_change
            if wait_time > 10.0:  # 10 seconds
                philosopher.stats['starvation_count'] += 1
                # Force release chopsticks to prevent starvation
                if philosopher.left_chopstick.owner == philosopher.id:
                    philosopher.left_chopstick.owner = None
                    philosopher.left_chopstick.in_hand = False
                    philosopher.left_chopstick.highlight = True
                if philosopher.right_chopstick.owner == philosopher.id:
                    philosopher.right_chopstick.owner = None
                    philosopher.right_chopstick.in_hand = False
                    philosopher.right_chopstick.highlight = True
                self._become_hungry(philosopher)  # Reset hunger
                self._set_action_text(philosopher, "Starving! Resetting...")
                self._log_event(philosopher.id, f"Starving! Waited {wait_time:.1f}s, releasing chopsticks")
                
                # For arbitration, increase priority
                if self.variation == SolutionVariation.RESOURCE_ARBITRATION:
                    philosopher.priority += 5
                    self._set_action_text(philosopher, f"Priority ↑ ({philosopher.priority})", 2.0)
                    self._log_event(philosopher.id, f"Priority increased to {philosopher.priority}")
            else:
                self._log_event(philosopher.id, f"Waiting for chopsticks ({wait_time:.1f}s)")
    
    def _finish_eating(self, philosopher):
        """Release chopsticks and return to thinking"""
        eat_duration = time.time() - philosopher.eating_start_time
        self._release_chopsticks(philosopher)
        philosopher.state = PhilosopherState.THINKING
        philosopher.last_state_change = time.time()
        philosopher.progress = 0.0
        philosopher.stats['eating_time'] += int(eat_duration)
        self._set_action_text(philosopher, "Finished eating")
        self._log_event(philosopher.id, f"Finished eating after {eat_duration:.1f}s, released chopsticks")
        
        # For arbitration, decrease priority after eating
        if self.variation == SolutionVariation.RESOURCE_ARBITRATION:
            philosopher.priority = max(1, philosopher.priority - 2)
            self._log_event(philosopher.id, f"Priority decreased to {philosopher.priority}")
    
    def _animate_chopstick_to_hand(self, chopstick, philosopher, is_left):
        """Animate chopstick moving to philosopher's hand"""
        # Set chopstick to be in hand
        chopstick.in_hand = True
        chopstick.hand_position = philosopher.hand_positions[0] if is_left else philosopher.hand_positions[1]
        
        # Small rotation for visual effect
        chopstick.angle += 0.1
    
    def _animate_chopstick_to_table(self, chopstick):
        """Animate chopstick moving back to table"""
        chopstick.in_hand = False
    
    def _acquire_chopsticks(self, philosopher):
        """Attempt to acquire both chopsticks based on current variation"""
        left, right = philosopher.left_chopstick, philosopher.right_chopstick
        
        # Highlight both chopsticks during attempt
        left.highlight = True
        right.highlight = True
        self.last_chopstick_move = time.time()
        
        if self.variation == SolutionVariation.DEADLOCK_PRONE:
            self._log_event(philosopher.id, "Attempting to pick left chopstick first (deadlock-prone)")
            # Basic deadlock-prone implementation
            if left.owner is None:
                left.owner = philosopher.id
                self._animate_chopstick_to_hand(left, philosopher, True)
                self._set_action_text(philosopher, "Picked left chopstick", 1.0)
                time.sleep(0.3 * (1/self.simulation_speed))  # Visual delay
                
                if right.owner is None:
                    right.owner = philosopher.id
                    self._animate_chopstick_to_hand(right, philosopher, False)
                    self._set_action_text(philosopher, "Picked right chopstick", 1.0)
                    return True
                else:
                    left.owner = None  # Release if can't get both
                    self._animate_chopstick_to_table(left)
                    self._set_action_text(philosopher, "Right chopstick busy", 1.0)
                    self._log_event(philosopher.id, "Right chopstick busy, releasing left")
            else:
                self._set_action_text(philosopher, "Left chopstick busy", 1.0)
                self._log_event(philosopher.id, "Left chopstick busy, can't eat")
            return False
        
        elif self.variation == SolutionVariation.WAITER_LOCK:
            self._log_event(philosopher.id, "Requesting seat from waiter")
            # Waiter limits to 4 philosophers at table
            if not self.waiter.acquire(blocking=False):
                self._set_action_text(philosopher, "Waiting for seat...", 1.0)
                self._log_event(philosopher.id, "No seats available, waiting")
                return False
            
            try:
                if left.owner is None and right.owner is None:
                    left.owner = philosopher.id
                    right.owner = philosopher.id
                    self._animate_chopstick_to_hand(left, philosopher, True)
                    self._animate_chopstick_to_hand(right, philosopher, False)
                    self._set_action_text(philosopher, "Got seat & chopsticks!", 1.0)
                    self._log_event(philosopher.id, "Got seat and both chopsticks")
                    return True
                self.waiter.release()
                self._set_action_text(philosopher, "Chopsticks busy", 1.0)
                self._log_event(philosopher.id, "Chopsticks busy, releasing seat")
                return False
            except:
                self.waiter.release()
                self._log_event(philosopher.id, "Error acquiring chopsticks, releasing seat")
                return False
        
        elif self.variation == SolutionVariation.ALTERNATE_PICKUP:
            # Even philosophers pick left then right, odd pick right then left
            if philosopher.id % 2 == 0:
                first, second = left, right
                first_in_hand, second_in_hand = True, False
                order = "left then right"
            else:
                first, second = right, left
                first_in_hand, second_in_hand = False, True
                order = "right then left"
            
            self._log_event(philosopher.id, f"Attempting {order} pickup")
            
            if first.owner is None:
                first.owner = philosopher.id
                self._animate_chopstick_to_hand(first, philosopher, first_in_hand)
                self._set_action_text(philosopher, f"Picked {order.split()[0]}", 1.0)
                time.sleep(0.3 * (1/self.simulation_speed))
                
                if second.owner is None:
                    second.owner = philosopher.id
                    self._animate_chopstick_to_hand(second, philosopher, second_in_hand)
                    self._set_action_text(philosopher, f"Picked {order.split()[2]}", 1.0)
                    self._log_event(philosopher.id, f"Successfully picked {order}")
                    return True
                else:
                    first.owner = None
                    self._animate_chopstick_to_table(first)
                    self._set_action_text(philosopher, f"{order.split()[2]} busy", 1.0)
                    self._log_event(philosopher.id, f"{order.split()[2]} chopstick busy")
            else:
                self._set_action_text(philosopher, f"{order.split()[0]} busy", 1.0)
                self._log_event(philosopher.id, f"{order.split()[0]} chopstick busy")
            return False
        
        elif self.variation == SolutionVariation.HIERARCHY_ENFORCED:
            # Always pick lower-numbered chopstick first
            first = left if left.id < right.id else right
            second = right if left.id < right.id else left
            first_in_hand = left.id < right.id
            second_in_hand = not first_in_hand
            
            self._log_event(philosopher.id, f"Attempting to pick chopstick {first.id} first (hierarchy)")
            
            if first.owner is None:
                first.owner = philosopher.id
                self._animate_chopstick_to_hand(first, philosopher, first_in_hand)
                self._set_action_text(philosopher, f"Picked chopstick {first.id}", 1.0)
                time.sleep(0.3 * (1/self.simulation_speed))
                
                if second.owner is None:
                    second.owner = philosopher.id
                    self._animate_chopstick_to_hand(second, philosopher, second_in_hand)
                    self._set_action_text(philosopher, f"Picked chopstick {second.id}", 1.0)
                    self._log_event(philosopher.id, f"Successfully picked both chopsticks {first.id} and {second.id}")
                    return True
                else:
                    first.owner = None
                    self._animate_chopstick_to_table(first)
                    self._set_action_text(philosopher, f"Chopstick {second.id} busy", 1.0)
                    self._log_event(philosopher.id, f"Chopstick {second.id} busy, releasing {first.id}")
            else:
                self._set_action_text(philosopher, f"Chopstick {first.id} busy", 1.0)
                self._log_event(philosopher.id, f"Chopstick {first.id} busy, can't eat")
            return False
        
        elif self.variation == SolutionVariation.ATOMIC_CHECK:
            # Try to atomically acquire both chopsticks
            self._log_event(philosopher.id, "Attempting atomic acquisition of both chopsticks")
            with self.global_lock:
                if left.owner is None and right.owner is None:
                    left.owner = philosopher.id
                    right.owner = philosopher.id
                    self._animate_chopstick_to_hand(left, philosopher, True)
                    self._animate_chopstick_to_hand(right, philosopher, False)
                    self._set_action_text(philosopher, "Got both chopsticks!", 1.0)
                    self._log_event(philosopher.id, "Atomically acquired both chopsticks")
                    return True
                self._set_action_text(philosopher, "Couldn't get both", 1.0)
                self._log_event(philosopher.id, "Couldn't atomically acquire both chopsticks")
            return False
        
        elif self.variation == SolutionVariation.RESOURCE_ARBITRATION:
            # Check if philosopher is at the front of both chopstick queues
            self._log_event(philosopher.id, f"Checking arbitration queues (Priority: {philosopher.priority})")
            
            if (left.requests and left.requests[0] == philosopher.id and
                right.requests and right.requests[0] == philosopher.id):
                
                if left.owner is None and right.owner is None:
                    left.owner = philosopher.id
                    right.owner = philosopher.id
                    self._animate_chopstick_to_hand(left, philosopher, True)
                    self._animate_chopstick_to_hand(right, philosopher, False)
                    self._set_action_text(philosopher, "Arbitrator granted!", 1.0)
                    self._log_event(philosopher.id, "Arbitrator granted both chopsticks")
                    return True
                else:
                    self._set_action_text(philosopher, "Resources busy", 1.0)
                    self._log_event(philosopher.id, "Chopsticks busy despite arbitration")
            else:
                self._set_action_text(philosopher, f"Waiting in queue (P:{philosopher.priority})", 1.0)
                self._log_event(philosopher.id, "Not at front of both queues yet")
            return False
    
    def _release_chopsticks(self, philosopher):
        """Release both chopsticks with visual feedback"""
        if philosopher.left_chopstick.owner == philosopher.id:
            philosopher.left_chopstick.owner = None
            philosopher.left_chopstick.in_hand = False
            philosopher.left_chopstick.highlight = True
            self._log_event(philosopher.id, "Released left chopstick")
        if philosopher.right_chopstick.owner == philosopher.id:
            philosopher.right_chopstick.owner = None
            philosopher.right_chopstick.in_hand = False
            philosopher.right_chopstick.highlight = True
            self._log_event(philosopher.id, "Released right chopstick")
        
        # Release waiter lock if using that variation
        if self.variation == SolutionVariation.WAITER_LOCK:
            self.waiter.release()
            self._log_event(philosopher.id, "Released seat back to waiter")
        
        self.last_chopstick_move = time.time()
    
    def _handle_click(self, pos):
        """Handle mouse clicks"""
        if self.show_help:
            self.show_help = False
            return
            
        # Check buttons
        for name, button in self.buttons.items():
            if button['rect'].collidepoint(pos):
                if name == 'start_pause':
                    self.is_running = not self.is_running
                    button['text'] = "Pause" if self.is_running else "Start"
                    self._log_event(0, f"Simulation {'paused' if not self.is_running else 'started'}")
                elif name == 'step':
                    self.step_mode = True
                    self._log_event(0, "Stepping simulation")
                elif name == 'reset':
                    self._initialize_simulation()
                    self.is_running = False
                    self.buttons['start_pause']['text'] = "Start"
                    self._log_event(0, "Simulation reset")
                elif name == 'speed_up':
                    self.simulation_speed = min(5.0, self.simulation_speed + 0.5)
                    self._log_event(0, f"Speed increased to {self.simulation_speed}x")
                elif name == 'slow_down':
                    self.simulation_speed = max(0.1, self.simulation_speed - 0.5)
                    self._log_event(0, f"Speed decreased to {self.simulation_speed}x")
                elif name == 'deadlock_prone':
                    self.variation = SolutionVariation.DEADLOCK_PRONE
                    self._initialize_simulation()
                    self._log_event(0, "Switched to Deadlock-Prone variation")
                elif name == 'waiter_lock':
                    self.variation = SolutionVariation.WAITER_LOCK
                    self._initialize_simulation()
                    self._log_event(0, "Switched to Waiter Lock variation")
                elif name == 'alternate_pickup':
                    self.variation = SolutionVariation.ALTERNATE_PICKUP
                    self._initialize_simulation()
                    self._log_event(0, "Switched to Alternate Pick-Up variation")
                elif name == 'hierarchy':
                    self.variation = SolutionVariation.HIERARCHY_ENFORCED
                    self._initialize_simulation()
                    self._log_event(0, "Switched to Hierarchy Enforced variation")
                elif name == 'atomic_check':
                    self.variation = SolutionVariation.ATOMIC_CHECK
                    self._initialize_simulation()
                    self._log_event(0, "Switched to Atomic Check variation")
                elif name == 'arbitration':
                    self.variation = SolutionVariation.RESOURCE_ARBITRATION
                    self._initialize_simulation()
                    self._log_event(0, "Switched to Resource Arbitration variation")
                elif name == 'show_stats':
                    self.show_stats = not self.show_stats
                    self._log_event(0, f"{'Showing' if self.show_stats else 'Hiding'} statistics")
                elif name == 'help':
                    self.show_help = True
                    self._log_event(0, "Help menu opened")
                elif name == 'show_logs':
                    self.logger.visible = not self.logger.visible
                    self._log_event(0, f"{'Showing' if self.logger.visible else 'Hiding'} logs")
                return
    
    def run(self):
        """Main application loop"""
        last_update = time.time()
        
        while True:
            current_time = time.time()
            delta_time = current_time - last_update
            last_update = current_time
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        self._handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.show_help = False
                    elif event.key == pygame.K_h:
                        self.show_help = not self.show_help
                    elif event.key == pygame.K_SPACE:
                        self.is_running = not self.is_running
                        self.buttons['start_pause']['text'] = "Pause" if self.is_running else "Start"
                    elif event.key == pygame.K_RIGHT:
                        self.step_mode = True
            
            # Update simulation
            if self.is_running or self.step_mode:
                self._update_philosophers()
            
            # Draw everything
            self.screen.fill(BACKGROUND_COLOR)
            
            # Draw table and items on right side
            self._draw_table()
            
            # Draw chopsticks first (under philosophers)
            for chopstick in self.chopsticks:
                self._draw_chopstick(chopstick)
            
            # Draw synchronization primitives on left side
            self._draw_sync_primitives()
            
            # Draw variation information on left side
            self._draw_variation_info()
            
            # Draw philosophers
            for philosopher in self.philosophers:
                self._draw_philosopher(philosopher)
            
            # Draw UI elements on left side
            self._draw_buttons()
            self._draw_stats()
            self._draw_logs()
            self._draw_help()
            
            # Display deadlock warning
            if self.deadlock_detected:
                warning = self.title_font.render("DEADLOCK DETECTED!", True, StateColor.DEADLOCK)
                warning_rect = warning.get_rect(center=(SCREEN_WIDTH//2, 30))
                pygame.draw.rect(self.screen, (50, 0, 0), (warning_rect.x-10, warning_rect.y-5, warning_rect.width+20, warning_rect.height+10), border_radius=5)
                self.screen.blit(warning, warning_rect)
            
            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    visualizer = DiningPhilosophersVisualizer()
    visualizer.run()