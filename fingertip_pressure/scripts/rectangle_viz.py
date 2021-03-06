#! /usr/bin/python

#***********************************************************
#* Software License Agreement (BSD License)
#*
#*  Copyright (c) 2009, Willow Garage, Inc.
#*  All rights reserved.
#*
#*  Redistribution and use in source and binary forms, with or without
#*  modification, are permitted provided that the following conditions
#*  are met:
#*
#*   * Redistributions of source code must retain the above copyright
#*     notice, this list of conditions and the following disclaimer.
#*   * Redistributions in binary form must reproduce the above
#*     copyright notice, this list of conditions and the following
#*     disclaimer in the documentation and/or other materials provided
#*     with the distribution.
#*   * Neither the name of the Willow Garage nor the names of its
#*     contributors may be used to endorse or promote products derived
#*     from this software without specific prior written permission.
#*
#*  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#*  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#*  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
#*  FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
#*  COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
#*  INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
#*  BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#*  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#*  CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#*  LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
#*  ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#*  POSSIBILITY OF SUCH DAMAGE.
#***********************************************************

# Author: Blaise Gassend

# Reads fingertip pressure data from /pressure and publishes it as a
# visualization_marker

import roslib
roslib.load_manifest('fingertip_pressure')
import rospy
import threading

from fingertip_pressure.msg import PressureInfo, PressureInfoElement
from pr2_msgs.msg import PressureState
from visualization_msgs.msg import Marker
from geometry_msgs.msg import Vector3
from fingertip_pressure.colormap import color

#def norm(v):
#    return sqrt(v.x * v.x + v.y * v.y + v.z * v.z)

class pressureVisualizer:
    def info_callback(self, info):
        self.lock.acquire()
        self.frame = []
        self.center = []
        self.hside1 = []
        self.hside2 = []
        for i in [0, 1]:
            self.frame.append(info.sensor[i].frame_id)
            self.center.append(info.sensor[i].center)
            self.hside1.append(info.sensor[i].halfside1)
            self.hside2.append(info.sensor[i].halfside2)
        self.got_info = True
        self.lock.release()
        #print "callback"

    def callback(self, pressurestate):
        self.lock.acquire()
        #print "callback"
        self.l_finger_tip = pressurestate.l_finger_tip
        self.r_finger_tip = pressurestate.r_finger_tip
        self.datatimestamp = pressurestate.header.stamp
        self.dataready = True
        self.lock.release()

    def publish(self):
        if self.dataready and self.got_info:
            self.lock.acquire()
            #print 'publish'
            self.dataready = False
            self.makeVisualization(self.l_finger_tip, 0)
            self.makeVisualization(self.r_finger_tip, 1)
            self.lock.release()

    def makeVisualization(self, data, tipnum):
        mk = Marker()
        mk.header.frame_id = self.frame[tipnum]
        mk.header.stamp = self.datatimestamp
        mk.ns = mk.header.frame_id + "/line"
        mk.type = Marker.LINE_STRIP
        mk.action = Marker.ADD
        #mk.lifetime = rospy.Duration(1)
        mk.points = []
        for i in range(0,5):
            mk.points.append(Vector3())
        #for i in range(0,1):
        for i in range(0,22):
            mk.id = i
            mk.pose.position = self.center[tipnum][i]
            mk.pose.orientation.w = 1.0
            mk.scale.x = 0.001
            h1 = self.hside1[tipnum][i]
            h2 = self.hside2[tipnum][i]
            mk.points[0].x =  h1.x + h2.x
            mk.points[1].x =  h1.x - h2.x  
            mk.points[2].x = -h1.x - h2.x
            mk.points[3].x = -h1.x + h2.x
            mk.points[0].y =  h1.y + h2.y
            mk.points[1].y =  h1.y - h2.y  
            mk.points[2].y = -h1.y - h2.y
            mk.points[3].y = -h1.y + h2.y
            mk.points[0].z =  h1.z + h2.z
            mk.points[1].z =  h1.z - h2.z  
            mk.points[2].z = -h1.z - h2.z
            mk.points[3].z = -h1.z + h2.z
            mk.points[4] = mk.points[0]
            mk.color.a = 1.0
            (mk.color.r, mk.color.g, mk.color.b) = color(data[i] / 6000.)
            #print "%f %f %f"%(mk.color.r, mk.color.g, mk.color.b)
            self.vis_pub.publish(mk)

    def __init__(self, source):
        self.got_info = False;
        self.dataready = False
        self.lock = threading.Lock()

        self.vis_pub = rospy.Publisher('visualization_marker', Marker)
        rospy.Subscriber(source, PressureState, self.callback)
        rospy.Subscriber(source + "_info", PressureInfo, self.info_callback)
        


if __name__ == '__main__':
    #@todo it would be nice to read an xml configuration file to get these parameters.
    rospy.init_node('pressure_sphere_viz')
    rospy.sleep(.2)
        
    pv1 = pressureVisualizer('pressure/r_gripper_motor')
    pv2 = pressureVisualizer('pressure/l_gripper_motor')
    
    while not rospy.is_shutdown():
        rospy.sleep(0.09)
        pv1.publish()
        pv2.publish()
