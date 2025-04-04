from typing import Dict, List, Tuple, Optional
from ..environments.static_maze import MazeEnvironment
from .team import Team
from .agent import Agent

class GameController:
    def __init__(self, maze: MazeEnvironment):
        """
        Initialize the game controller.
        """
        self.maze = maze
        self.teams: Dict[int, Team] = {}
        self.current_turn = 0
        self.game_over = False
        self.winning_team: Optional[int] = None
    
    def add_team(self, team_id: int, color: str = None, selfishness: float = 0.0) -> Team:
        """
        Create and add a new team.
        """
        team = Team(team_id, color, selfishness=selfishness)
        self.teams[team_id] = team
        return team
    
    def initialize_teams(self):
        """
        Initialize teams and their agents based on maze start positions.
        """
        next_agent_id = 0
        
        for team_id, start_positions in self.maze.start_positions.items():
            if team_id not in self.teams:
                self.add_team(team_id)
            
            # Create agents at start positions
            for x, y in start_positions:
                agent = Agent(next_agent_id, team_id, x, y)
                self.teams[team_id].add_agent(agent)

                # Update discovered tiles based on the start position
                visible_tiles = self.maze.get_visible_tiles(x, y, agent.vision_range)
                agent.update_discovered_tiles(visible_tiles)

                next_agent_id += 1
    
    def move_agent(self, agent_id: int, team_id: int, dx: int, dy: int) -> bool:
        """
        Attempt to move an agent. True if the move was successful, False otherwise
        """
        if team_id not in self.teams:
            return False
        
        team = self.teams[team_id]
        if agent_id not in team.agents:
            return False

        agent = team.agents[agent_id]
        new_x, new_y = agent.move(dx, dy)
    
        # Check if the move is valid
        if not self.maze.is_valid_move(new_x, new_y):
            return False
    
        # Check if there's an agent from another team on the target tile
        for other_team_id, other_team in self.teams.items():
            if other_team_id != team_id:
                for other_agent in other_team.agents.values():
                    if other_agent.x == new_x and other_agent.y == new_y:
                        return False
    
        # If we get here, the move is valid
        agent.update_position(new_x, new_y)
    
        # Update discovered tiles based on the new position
        visible_tiles = self.maze.get_visible_tiles(new_x, new_y, agent.vision_range)
        agent.update_discovered_tiles(visible_tiles)
    
        # Check if agent reached the goal
        if self.maze.goal_position:
            agent.check_goal_reached(self.maze.goal_position)
    
        return True
    
    def check_win_conditions(self):
        """
        Check if any team has won.
        """
        if not self.maze.goal_position:
            return
        
        for team_id, team in self.teams.items():
            if team.has_won(self.maze.goal_position):
                self.game_over = True
                self.winning_team = team_id
                break
    
    def update(self):
        """
        Update game state for a single turn.
        """
        if self.game_over:
            return
        
            # If maze has dynamic elements, update them
        if hasattr(self.maze, 'update_dynamic_walls'):
            self.maze.update_dynamic_walls()
        
        # Update agent vision based on current positions
        for team in self.teams.values():
            for agent in team.agents.values():
                visible_tiles = self.maze.get_visible_tiles(agent.x, agent.y, agent.vision_range)
                agent.update_discovered_tiles(visible_tiles)
                agent.check_goal_reached(self.maze.goal_position)
            team.share_vision()
        
        # Check win conditions
        self.check_win_conditions()
        
        # Increment turn counter
        self.current_turn += 1
    
    def get_game_state(self):
        """
        Get the current state of the game.
        """
        return {
            "turn": self.current_turn,
            "teams": {team_id: {
                "agent_positions": team.get_agent_positions(),
                "discovered_tiles": list(team.get_discovered_tiles())
            } for team_id, team in self.teams.items()},
            "game_over": self.game_over,
            "winning_team": self.winning_team
        }
    
    def __str__(self):
        """
        String representation of the game state.
        """
        game_str = f"Turn: {self.current_turn}\n"
        game_str += f"Teams: {len(self.teams)}\n"
        
        for team_id, team in self.teams.items():
            game_str += f"- {team}\n"
            for agent_id, agent in team.agents.items():
                game_str += f"  - {agent}\n"
        
        if self.game_over:
            game_str += f"Game over! Team {self.winning_team} wins!\n"
        
        return game_str
