#!/usr/bin/env python

# Author: christoph.roesmann@tu-dortmund.de

import rospy, math
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path


def publish_via_points_msg():
  pub = rospy.Publisher('/move_base/TebLocalPlannerROS/via_points', Path, queue_size=1)
  rospy.init_node("test_via_points_msg")


  via_points_msg = Path() 
  via_points_msg.header.stamp = rospy.Time.now()
  via_points_msg.header.frame_id = "map" # CHANGE HERE: odom/map
  
  # Add via-points
  point1 = PoseStamped()
  point1.pose.position.x = 7.0
  point1.pose.position.y = 0.3

  point2 = PoseStamped()
  point2.pose.position.x = 6.0
  point2.pose.position.y = -0.3

  point3 = PoseStamped()
  point3.pose.position.x = 5.0
  point3.pose.position.y = 0.0

  via_points_msg.poses = [point1, point2, point3]

  r = rospy.Rate(1) # 10hz
  t = 0.0

  # pub.publish(via_points_msg)
  # r.sleep()
  # pub.publish(via_points_msg)
  # r.sleep()

  while not rospy.is_shutdown():
        
    pub.publish(via_points_msg)
    
    r.sleep()



if __name__ == '__main__': 
  try:
    publish_via_points_msg()
  except rospy.ROSInterruptException:
    pass

