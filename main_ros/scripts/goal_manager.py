#!/usr/bin/env python


import rospy
import math
import actionlib
import tf
from tf.transformations import quaternion_from_euler, euler_from_quaternion
from ar_track_alvar_msgs.msg import AlvarMarkers
from geometry_msgs.msg import PoseStamped
from move_base_msgs.msg import MoveBaseActionResult, MoveBaseAction


class GoalManager:
    def __init__(self):
        rospy.init_node("goal_manager", anonymous=True)
        self.goal_cnt = 0
        # self.goal_list = [[5, 0, 0], [10, 0, 90], "parking"]
        self.goal_list = ["parking"]
        self.goal_num = len(self.goal_list)

        self.rate = rospy.Rate(10)

        self.goal_pub = rospy.Publisher("/move_base_simple/goal", PoseStamped, queue_size=1)
        self.res_sub = rospy.Subscriber("/move_base/result", MoveBaseActionResult, self.reach_cb)
        self.tf_listener = tf.TransformListener()

        client = actionlib.SimpleActionClient('move_base',MoveBaseAction)
        client.wait_for_server()

        rospy.loginfo("Goal Manager Initialized.")

        self.goal_pub.publish(self.goal_msg_generate())
        rospy.spin()


    def goal_msg_generate(self):
        goal = PoseStamped()
        goal.header.frame_id = "map"
        goal.header.stamp = rospy.Time.now()

        target = self.goal_list[self.goal_cnt]

        if type(target) == list:
            goal.pose.position.x = target[0]
            goal.pose.position.y = target[1]

            x, y, z, w = quaternion_from_euler(0, 0, math.radians(target[2]))
            goal.pose.orientation.x = x
            goal.pose.orientation.y = y
            goal.pose.orientation.z = z
            goal.pose.orientation.w = w
        
        elif target == "parking":
            alvar_msg = rospy.wait_for_message("/ar_pose_marker", AlvarMarkers, timeout=3)

            if len(alvar_msg.markers) != 1:
                rospy.logwarn("Two or MoreMarkers or No Marker.")
                
            else:
                target_frame = "ar_marker_"+str(alvar_msg.markers[0].id)
                src_frame = "map"

                self.tf_listener.waitForTransform(target_frame, src_frame, rospy.Time(), rospy.Duration(1.0))
                try:
                    now = rospy.Time.now()
                    self.tf_listener.waitForTransform(target_frame, src_frame, now, rospy.Duration(1.0))
                    trans, rot = self.tf_listener.lookupTransform(target_frame, src_frame, now)
                except Exception as E:
                    rospy.logwarn(E)
                    
                goal.pose.position.x = trans[0]
                goal.pose.position.y = trans[2]

                _,_, yaw = euler_from_quaternion(rot)
                x, y, z, w = quaternion_from_euler(0, 0, yaw)
                goal.pose.orientation.x = x
                goal.pose.orientation.y = y
                goal.pose.orientation.z = z
                goal.pose.orientation.w = w

        return goal


    def reach_cb(self, msg):
        if msg.status.text == "Goal reached.":
            self.goal_cnt += 1

            if self.goal_cnt >= self.goal_num:
                rospy.loginfo("Mission Finished.")
                exit(0)
            
            else:
                self.goal_pub.publish(self.goal_msg_generate())

        else:
            self.goal_pub.publish(self.goal_msg_generate())


if __name__ == "__main__":
    try:
        a = GoalManager()
    except KeyboardInterrupt:
        exit(0)