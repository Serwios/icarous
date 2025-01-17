import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import patches
from matplotlib import text
from math import sin,cos,atan2,pi
import numpy as np
import math
from scipy import interpolate

class AgentAnimation():
    def __init__(self,xmin,ymin,xmax,ymax,traces=True,playbkspeed=1,interval=5,record=False,filename=""):
        self.fig = plt.figure(frameon=True)
        plt.xlabel("x [m]")
        plt.ylabel("y [m]")

        self.ax = plt.axes(xlim=(xmin, xmax), ylim=(ymin, ymax))
        self.paths = {}
        self.agents = []
        self.agentsRadius = {}
        self.agentNames = []
        self.agentLines = []
        self.data = {}
        self.interval = interval
        self.circle = {}
        self.bands = {}
        self.record = record
        self.status  = {}
        self.filename = filename
        self.speed = playbkspeed
        self.minlen = 0
        self.tmin = 0
        self.tmax = 0
        self.dt = -1
        self.agentIndex = {}
        self.traces = traces

    def AddAgent(self,name,radius,color,data,show_circle=False,circle_rad = 10):
        #agt = plt.Circle((0.0, 0.0), radius=radius, fc=color)
        if len(data['time']) < 2:
            return

        if name not in self.agentNames:
            self.agentNames.append(name)
            self.data[name] = data
            agt = self.GetTriangle(radius,(0.0,0,0),(1.0,0.0),color)
            self.ax.add_patch(agt)
            self.agents.append(agt)
            self.agentIndex[name] = 0
        else:
            t0 = self.data[name]['time'][0]
            t1 = self.data[name]['time'][-1]
            index = 0
            if data['time'][0] < t0:
                for key in data.keys():
                    self.data[name][key]= data[key] + self.data[name][key]
            else:
                while data['time'][index] < t1:
                    index = index + 1
                    if index >= len(data['time']):
                        return
                for key in data.keys():
                    self.data[name][key].extend(data[key][index:])
        self.tmin = min(self.tmin,data['time'][0])
        self.tmax = max(self.tmax,data['time'][-1])
        if self.dt < 0:
            self.dt = data['time'][1] - data['time'][0]
        self.minlen = max(self.minlen,len(data['positionNED']))
        positionNED = np.array(self.data[name]['positionNED'])
        velocityNED = np.array(self.data[name]['velocityNED'])
        time = self.data[name]['time']
        self.data[name]['positionNED_intp'] = [interpolate.interp1d(time,positionNED[:,0],bounds_error=False,fill_value=(positionNED[0][0],positionNED[-1][0])),
                                               interpolate.interp1d(time,positionNED[:,1],bounds_error=False,fill_value=(positionNED[0][1],positionNED[-1][1])),
                                               interpolate.interp1d(time,positionNED[:,2],bounds_error=False,fill_value=(positionNED[0][2],positionNED[-1][2]))]
        self.data[name]['velocityNED_intp'] = [interpolate.interp1d(time,velocityNED[:,0],bounds_error=False,fill_value=(0,0)),
                                               interpolate.interp1d(time,velocityNED[:,1],bounds_error=False,fill_value=(0,0)),
                                               interpolate.interp1d(time,velocityNED[:,2],bounds_error=False,fill_value=(0,0))]
        self.data[name]['reverseTime_intp'] = interpolate.interp1d(time,np.arange(len(time)),bounds_error=False,fill_value=(0,len(time)-1))
        self.data[name]['plotX'] = []
        self.data[name]['plotY'] = []
        if self.traces:
            line, = plt.plot(0,0)
            self.paths[name] = line
        self.agentsRadius[name] = radius
        if show_circle:
            circlePatch = plt.Circle((0, 0), radius=circle_rad, fc='y',alpha=0.5)
            self.circle[name] = circlePatch
            self.ax.add_patch(circlePatch)
            # Draw bands
            sectors = []
            for i in range(10):
                ep = patches.Wedge((0,0),circle_rad,theta1=0,theta2=0,fill=True,alpha=0.6)
                sectors.append(ep)
                self.ax.add_patch(ep)
            self.bands[name] = sectors

    def AddZone(self,xy,radius,color):
        circlePatch = patches.Arc((xy[0], xy[1]), width=2*radius,height =2*radius, fill =False, color=color)
        self.ax.add_patch(circlePatch)

    def GetTriangle(self, tfsize, pos, vel, col):
        x = pos[0]
        y = pos[1]

        t = atan2(vel[1],vel[0])

        x1 = x + 2*tfsize * cos(t)
        y1 = y + 2*tfsize * sin(t)

        tempX = x - tfsize * cos(t)
        tempY = y - tfsize * sin(t)

        x2 = tempX + tfsize * cos((t + pi/2))
        y2 = tempY + tfsize * sin((t + pi/2))

        x3 = tempX - tfsize * cos((t + pi/2))
        y3 = tempY - tfsize * sin((t + pi/2))


        triangle = plt.Polygon([[x1, y1], [x2, y2], [x3, y3]], color=col, fill=True)
        triangle.labelText = plt.text(x+2*tfsize, y+2*tfsize, "", fontsize=8)

        return triangle

    def UpdateTriangle(self,tfsize, pos, vel, poly):
        x = pos[0]
        y = pos[1]
        z = pos[2]

        t = atan2(vel[1], vel[0])

        x1 = x + 2*tfsize * cos(t)
        y1 = y + 2*tfsize * sin(t)

        tempX = x - 1*tfsize * cos(t)
        tempY = y - 1*tfsize * sin(t)

        x2 = tempX + 1*tfsize * cos((t + pi/2))
        y2 = tempY + 1*tfsize * sin((t + pi/2))

        x3 = tempX - 1*tfsize * cos((t + pi/2))
        y3 = tempY - 1*tfsize * sin((t + pi/2))

        poly.set_xy([[x1, y1], [x2, y2], [x3, y3]])
        poly.labelText.set_position((x + 2*tfsize,y+2*tfsize))
        speed = np.sqrt(vel[0]**2 + vel[1]**2)
        poly.labelText.set_text('Z:%.2f[m]\nS:%.2f[mps]' % (z,speed))

    def AddPath(self,path,color1,points = [],labels = [],color2=''):
        if (path.shape[0] < 2):
            return
        if len(points) > 0:
            plt.plot(points[:,1],points[:,0],color1)
        else:
            plt.plot(path[:,1],path[:,0],color1)
        if color2 == '':
            plt.scatter(path[:,1],path[:,0])
        else:
            plt.scatter(path[:,1],path[:,0],c=color2)
        #for i,label in enumerate(labels):
        #    plt.text(path[i,1],path[i,0],','.join(label))

    def AddFence(self,fence,color):
        plt.plot(fence[:,1],fence[:,0],color)
        plt.scatter(fence[:,1],fence[:,0])

    def UpdateBands(self,position,bands,timeLookUp,t,sectors):
        i = int(timeLookUp(t))
        numBands = bands["numBands"][i]
        if(numBands) == 0:
            return
        low      = bands["low"][i]
        high     = bands["high"][i]
        btype    = bands["bandTypes"][i]
        h2c = lambda x:np.mod((360 -  (x - 90)),360)
        for sector in sectors:
            sector.set_theta1(0)
            sector.set_theta2(0)
            sector.set_center((0,0))
            sector.set_alpha(0)
        for i in range(numBands):
            max = h2c(low[i])
            min = h2c(high[i])
            if btype[i] != 1:
                if btype[i] == 4:
                    color = 'r'
                elif btype[i] == 5:
                    color = 'g'
                else:
                    color = 'b'
                sectors[i].set_center(position[:2])
                sectors[i].set_theta1(min)
                sectors[i].set_theta2(max)
                sectors[i].set_color(color)
                sectors[i].set_alpha(0.6)


    def init(self):
        return self.agents,self.paths,self.circle

    def animate(self,time,i):
        i = int(i*self.speed)
        print("generating animation: %.1f%%" % (i/self.minlen*100), end="\r")
        if i < self.minlen-1:
            for j, vehicle in enumerate(self.agents):
                k = time[i]
                id = self.agentNames[j]
                #vehicle.center = (self.data[id][i][0], self.data[id][i][1])
                
                position = (self.data[id]["positionNED_intp"][1](k), self.data[id]["positionNED_intp"][0](k),self.data[id]["positionNED_intp"][2](k))
                velocity = (self.data[id]["velocityNED_intp"][1](k), self.data[id]["velocityNED_intp"][0](k),self.data[id]["velocityNED_intp"][2](k))
                if np.linalg.norm(velocity) < 1e-3:
                    continue
                self.data[id]['plotX'].append(float(position[0]))
                self.data[id]['plotY'].append(float(position[1]))
                
                radius = self.agentsRadius[id]
                self.UpdateTriangle(radius,position,velocity,vehicle)
                if self.traces:
                    self.paths[id].set_xdata(self.data[id]['plotX'])
                    self.paths[id].set_ydata(self.data[id]['plotY'])
                if "trkbands" in self.data[id].keys():
                    self.UpdateBands(position,self.data[id]["trkbands"],self.data[id]["reverseTime_intp"],k,self.bands[id])
                if id in self.circle.keys():
                    if self.circle[id] is not None:
                        self.circle[id].center = position
        else:
            plt.close(self.fig)
        return self.agents,self.paths,self.circle

    def run(self):
        time = np.arange(self.tmin,self.tmax+self.dt,self.dt)
        animate = lambda x: self.animate(time,x)
        init = lambda:self.init()
        self.anim = animation.FuncAnimation(self.fig, animate,
                                       init_func=init,
                                       frames=self.minlen,
                                       interval=self.interval,
                                       repeat = False,
                                       blit=False)
        
        # Save animation as a movie
        if self.record:
            self.anim.save(self.filename, writer= "ffmpeg", fps=60)
        else:
            #plt.axis('off')
            plt.show()
