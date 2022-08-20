#!/usr/bin/env python


import rospy
import math
import actionlib
import tf
import threading
from tf.transformations import quaternion_from_euler
from ar_marker_pose import ar_marker_pose

from ar_track_alvar_msgs.msg import AlvarMarkers
from geometry_msgs.msg import PoseStamped
from move_base_msgs.msg import MoveBaseActionResult, MoveBaseAction, MoveBaseActionGoal, MoveBaseFeedback
from nav_msgs.msg import Path
from std_srvs.srv import Empty
# from actionlib_msgs.msg import GoalID


class GoalManager:
    def __init__(self):
        self.goal_cnt = 0
        self.goal_list = [[6, 0, 0, 0], [8, 0, 30, None]] #x,y,yaw, via_point_num
        self.via_points = [[(2, 0.3), (4, -0.3), (6, 0)]]
        # self.goal_list = [("p_parking", [0, -0.5, 90])]
        self.goal_num = len(self.goal_list)

        self.rate = rospy.Rate(10)

        # self.cancel_pub = rospy.Publisher("/move_base/cancel", GoalID, queue_size=1)
        self.goal_pub = rospy.Publisher("/move_base/goal", MoveBaseActionGoal, queue_size=1)
        self.feedback_sub = rospy.Publisher("/move_base/feedback", MoveBaseFeedback, self.proximity_cb)
        self.res_sub = rospy.Subscriber("/move_base/result", MoveBaseActionResult, self.reach_cb)
        self.via_pub = rospy.Publisher('/move_base/TebLocalPlannerROS/via_points', Path, queue_size=1)
        self.stop_line = False
        self.tf_listener = tf.TransformListener()
        self.via_point_thread = None

        client = actionlib.SimpleActionClient('move_base', MoveBaseAction)
        client.wait_for_server()

        rospy.loginfo("Goal Manager Initialized.")

        if type(self.goal_list[self.goal_cnt]) == list and self.goal_list[self.goal_cnt][3] is not None:
            rospy.loginfo("Thread Initialized!")
            self.via_point_thread = threading.Thread(target=self.via_points_pub, args=(self.via_points[self.goal_list[self.goal_cnt][3]], ))
            self.via_point_thread.start()

        self.goal_pub.publish(self.goal_msg_generate())
        rospy.spin()

    def via_points_pub(self, via_points):
        via_points_msg = Path() 
        via_points_msg.header.stamp = rospy.Time.now()
        via_points_msg.header.frame_id = "odom" # CHANGE HERE: odom/map
        
        # Add via-points
        for point in via_points:
            point_msg = PoseStamped()
            point_msg.pose.position.x = point[0]
            point_msg.pose.position.y = point[1]
            via_points_msg.poses.append(point_msg)

        r = rospy.Rate(5) # 10hz
        t = 0.0

        while 1:
            self.via_pub.publish(via_points_msg)
            print("pub")
            r.sleep()


    def goal_msg_generate(self):
        goal = MoveBaseActionGoal()
        goal.header.frame_id = "map"
        goal.header.stamp = rospy.Time.now()
        goal.header.seq = self.goal_cnt
        goal.goal_id.id = str(self.goal_cnt)

        target = self.goal_list[self.goal_cnt]

        goal.goal.target_pose.header.frame_id = "map"
        goal.goal.target_pose.header.stamp.secs = goal.header.stamp.secs
        goal.goal.target_pose.header.stamp.nsecs = goal.header.stamp.nsecs
        goal.goal.target_pose.header.seq = self.goal_cnt

        if type(target) == list:
            goal.goal.target_pose.pose.position.x = target[0]
            goal.goal.target_pose.pose.position.y = target[1]

            x, y, z, w = quaternion_from_euler(0, 0, math.radians(target[2]))
            goal.goal.target_pose.pose.orientation.x = x
            goal.goal.target_pose.pose.orientation.y = y
            goal.goal.target_pose.pose.orientation.z = z
            goal.goal.target_pose.pose.orientation.w = w
        
        elif target[0] == "p_parking":
            alvar_msg = rospy.wait_for_message("/ar_pose_marker", AlvarMarkers, timeout=3)

            if len(alvar_msg.markers) != 1:
                rospy.logwarn("Two or MoreMarkers or No Marker.")
                
            else:
                trans = ar_marker_pose(self.tf_listener, alvar_msg.markers[0].id)
                
                goal.goal.target_pose.pose.position.x = trans[0] + target[1][0]
                goal.goal.target_pose.pose.position.y = trans[1] + target[1][1]
                
                target_rot = quaternion_from_euler(0, 0, math.radians(target[1][2]))
                goal.goal.target_pose.pose.orientation.x = target_rot[0]
                goal.goal.target_pose.pose.orientation.y = target_rot[1]
                goal.goal.target_pose.pose.orientation.z = target_rot[2]
                goal.goal.target_pose.pose.orientation.w = target_rot[3]

        elif target == "t_parking":
            alvar_msg = rospy.wait_for_message("/ar_pose_marker", AlvarMarkers, timeout=3)

            if len(alvar_msg.markers) != 1:
                rospy.logwarn("Two or MoreMarkers or No Marker.")

            pass
        
        elif target == "stop_line":
            pass
        
        rospy.loginfo("#%d: %f %f %f", self.goal_cnt, target[0], target[1], target[2])
        return goal


    # def reach_cb(self, msg):
    #     print(msg)
    #     if msg.status.text == "Goal reached." and int(msg.status.goal_id.id) == self.goal_cnt:
    #         self.goal_cnt += 1

    #         clearing = rospy.ServiceProxy('/move_base/clear_costmaps', Empty)
    #         res = clearing()

    #         if self.via_point_thread is not None:
    #             self.via_point_thread.join()
    #             self.via_point_thread = None

    #         if self.goal_cnt >= self.goal_num:
    #             rospy.loginfo("Mission Finished.")
    #             exit(0)
            
    #         else:
    #             if type(self.goal_list[self.goal_cnt]) == list and self.goal_list[self.goal_cnt][3] is not None:
    #                 self.via_point_thread = threading.Thread(target=self.via_points_pub, args=(self.via_points[self.goal_list[self.goal_cnt][3]]))
    #                 self.via_point_thread.start()

    #             self.goal_pub.publish(self.goal_msg_generate())

    #     else:
    #         self.goal_pub.publish(self.goal_msg_generate())

    def reach_cb(self, msg):
        print(msg)
        if msg.status.text == "Goal reached." and int(msg.status.goal_id.id) == self.goal_cnt:
            self.goal_cnt += 1

            clearing = rospy.ServiceProxy('/move_base/clear_costmaps', Empty)
            res = clearing()

            if self.goal_cnt >= self.goal_num:
                rospy.loginfo("Mission Finished.")
                exit(0)

        else:
            self.goal_pub.publish(self.goal_msg_generate())

    def proximity_cb(self, msg):
        print(msg)
        if type(self.goal_list[self.goal_cnt]) == list and [msg.position.x, msg.position.y, msg.position.z] == self.goal_list[self.goal_cnt][:3]: #goal coordinates
            if self.via_point_thread is not None:
                self.via_point_thread.join()
                self.via_point_thread = None
            
            else:
                if type(self.goal_list[self.goal_cnt]) == list and self.goal_list[self.goal_cnt][3] is not None:
                    self.via_point_thread = threading.Thread(target=self.via_points_pub, args=(self.via_points[self.goal_list[self.goal_cnt][3]]))
                    self.via_point_thread.start()
        else:
            self.goal_pub.publish(self.goal_msg_generate())

if __name__ == "__main__":
    try:
        rospy.init_node("goal_manager", anonymous=True)
        a = GoalManager()
    except KeyboardInterrupt:
        exit(0)