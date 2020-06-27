from roar_autonomous_system.agents.agent import Agent
from pathlib import Path
from roar_autonomous_system.control.pid_controller import VehiclePIDController
from roar_autonomous_system.planning.local_planners.simple_path_following_local_planner import \
    SimplePathFollowingLocalPlanner
from roar_autonomous_system.planning.behavior_planners.no_action_behavior_planner import NoActionBehaviorPlanner
from roar_autonomous_system.planning.mission_planners.path_following_mission_planner import PathFollowingMissionPlanner
from roar_autonomous_system.control.util import PIDParam
from roar_autonomous_system.util.models import Control, Vehicle, SensorData
from bridges.bridge import Bridge
import logging


class PathFollowingAgent(Agent):
    def __init__(self, vehicle, route_file_path: Path, bridge: Bridge, target_speed=20):
        super().__init__(vehicle, bridge)
        self.logger = logging.getLogger("PathFollowingAgent")
        self.route_file_path = route_file_path
        self.pid_controller = VehiclePIDController(vehicle=vehicle,
                                                   args_lateral=PIDParam.default_lateral_param(),
                                                   args_longitudinal=PIDParam.default_longitudinal_param(),
                                                   target_speed=target_speed)
        self.mission_planner = PathFollowingMissionPlanner(file_path=self.route_file_path)
        self.behavior_planner = NoActionBehaviorPlanner(mission_path=self.mission_planner.mission_plan)
        self.local_planner = SimplePathFollowingLocalPlanner(vehicle=vehicle,
                                                             controller=self.pid_controller,
                                                             mission_planner=self.mission_planner,
                                                             behavior_planner=self.behavior_planner.generate_constraints(),
                                                             closeness_threshold=1)
        self.logger.debug(f"Path Following Agent Initiated. Reading from {route_file_path.as_posix()}")

    def run_step(self, vehicle: Vehicle, sensor_data: SensorData) -> Control:
        self.sync(vehicle=vehicle, sensor_data=sensor_data)
        if self.local_planner.is_done():
            control = Control()
            self.logger.debug("Path Following Agent is Done. Idling.")
        else:

            control = self.local_planner.run_step()
        return control

    def sync(self, vehicle: Vehicle, sensor_data: SensorData):
        super(PathFollowingAgent, self).sync(vehicle=vehicle, sensor_data=sensor_data)
        self.local_planner.vehicle = self.vehicle  # on every run step, sync vehicle with lower level
