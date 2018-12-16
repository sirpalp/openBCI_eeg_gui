# --General packages--
import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from PyQt5 import QtCore
from pynput import keyboard
# -- My packages --
from app.colors import *
from app.activation_b import btn
from ... dock.dock import Dock
# To draw the brain
from .object_3D_creator import Obj3DCreator
from save.data_saver import DataSaver
from .sphere import Sphere
from .brain import Brain
from .plane import Plane
from app.pyqt_frequently_used import (create_gr, create_txt_label,
                                      create_splitter, create_param_combobox,
                                      TripletBox)
import mne
from mne.surface import decimate_surface  # noqa
from pyqtgraph.Qt import QtCore


class Viz3D(Dock):
    def __init__(self, gv, layout):
        secondary_gr, secondary_layout = create_gr()
        super().__init__(gv, 'viz', secondary_layout)
        self.gv = gv
        self.layout = layout

        self.len_sig = 100

        self.init_viz_layout()
        self.init_modify_curve_layout()
        self.init_layout()

        self.electrod_sphere = Sphere(
                self.gv, scaling_factor=3, update_func_name='follow_plane')
        self.view.addItem(self.electrod_sphere.item)


        self.plane_x, self.plane_y, self.plane_z = self.create_planes()
        self.electrod_sphere.set_element_to_follow(
            ele_to_follow=[self.plane_x.pos, self.plane_y.pos,
                           self.plane_z.pos],)

        self.sphere = Sphere(self.gv, scaling_factor=48)

        self.show_3D_viz_b()

        self.line_item = {}
        self.create_plot_lines()

        # self.on_off_button()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)

    def show_3D_viz_b(self):
        btn('Show 3D', self.layout, (1, 0),
            func_conn=self.show_3D_viz, color=grey3, txt_color=white)

    def show_3D_viz(self):
        self.create_head()
        self.create_total_brain()

    def create_head(self):
        path = mne.datasets.sample.data_path()
        surf = mne.read_bem_surfaces(path + '/subjects/sample/bem/sample-head.fif')[0]
        points, triangles = surf['rr'], surf['tris']
        # reduce to 30000 triangles:
        points_dec, triangles_dec = decimate_surface(
                points, triangles, n_triangles=30000)
        p, t = points_dec, triangles_dec
        mesh_data = gl.MeshData(p, t)
        mesh_item = gl.GLMeshItem(
                meshdata=mesh_data, computeNormals=True,
                shader='viewNormalColor', glOptions='translucent')
        mesh_item.translate(0, 0, -20)
        mesh_item.rotate(90, 1, 0, 0)
        mesh_item.scale(650, 650, 650)
        mesh_item.setColor([0, 0, 1, 0.4])
        # s.setData(=p)
        self.view.addItem(mesh_item)

    def create_planes(self):
        plane_x = Plane(
                self.gv, axis='x', mvt=np.array([1, 0, 0]), key=('j', 'k'),
                rotation=(90, 0, 1, 0), color=(0, 0, 255, 4),
                triplet_box=self.triplet_box)
        plane_y = Plane(
                self.gv, axis='y', mvt=np.array([0, 1, 0]), key=('j', 'k'),
                rotation=(90, 1, 0, 0), color=(0, 255, 0, 4),
                triplet_box=self.triplet_box)
        plane_z = Plane(
                self.gv, axis='z', mvt=np.array([0, 0, 1]), key=('j', 'k'),
                color=(255, 0, 0, 4), triplet_box=self.triplet_box)
        self.view.addItem(plane_z.item)
        self.view.addItem(plane_y.item)
        self.view.addItem(plane_x.item)

        return plane_x, plane_y, plane_z

    def init_viz_layout(self):
        # viz_gr, viz_layout = create_gr()
        self.view = self.init_view()
        self.layout.addWidget(self.view, 2, 0, 1, 9)

    def init_modify_curve_layout(self):
        # modify_curve_gr, modify_curve_layout = create_gr()
        create_param_combobox(
                self.layout, 'Ch to move', (0, 1, 1, 1),                       # TODO: ALEXM: change to have a hboxlayout instead of a qboxlayout
                [str(ch+1) for ch in range(self.gv.N_CH)], self.print_shit,
                cols=1, editable=False)
        # Position
        pos_l = create_txt_label('Position')
        self.layout.addWidget(pos_l, 0, 2, 1, 3)
        self.triplet_box = TripletBox(
                self.gv, name='position', col=2, layout=self.layout,
                colors=(blue_plane, green_plane, red_plane))
        # Angle
        angle_l = create_txt_label('Angle')
        self.layout.addWidget(angle_l, 0, 5, 1, 3)
        self.triplet_angle = TripletBox(
                self.gv, name='angle', col=5, layout=self.layout)
        # Save to file
        DataSaver(
                self.gv.main_window, self.gv, self.layout,                         # TODO: ALEXM: Add a tooltip
                saving_type='Save', pos=(0, 8), size=(1, 1),
                save_file_button=False, choose_b_size=(1, 1))
        # return modify_curve_layout, modify_curve_gr

    def init_color_button(self):
        color_b = pg.ColorButton(close_fit=True)
        color_b.sigColorChanging.connect(self.print_shit)
        color_b.sigColorChanged.connect(self.print_shit)
        return color_b

    def print_shit(self):
        print('shizzle')

    def init_layout(self):
        self.init_on_off_button()
        # splitter = create_splitter(self.viz_gr, self.modify_curve_gr)
        # self.layout.addWidget(splitter, 0, 0)

    def create_total_brain(self):
        self.brain_v = Brain()
        self.brain_v.volume(show_box=False, show_axis=False)
        self.view.addItem(self.brain_v.volume)
        self.brain_s = Brain()
        self.brain_s.scatter()
        self.view.addItem(self.brain_s.volume)

    def create_plot_lines(self):
        for n in range(self.gv.N_CH):
            self.line_item[n] = gl.GLLinePlotItem()
            self.view.addItem(self.line_item[n])
            self.line_item[n].translate(-self.len_sig - self.sphere.radius,
                                        0, 0)
            print('pos', self.line_item[n].pos)
            self.line_item[n].rotate(20*(n+1), 0, 1, 0)

    def init_view(self):
        """     """
        view = gl.GLViewWidget()
        view.opts['distance'] = 300
        view.opts['azimuth'] = 40
        view.opts['elevation'] = 15
        return view

    def set_plotdata(self, name, points, color, width):
        self.line_item[name].setData(pos=points, color=color, width=width)

    def update(self):
        for ch in range(self.gv.N_CH):
            pts = np.stack((
                    np.linspace(0, self.len_sig, self.gv.DEQUE_LEN),
                    np.zeros(self.gv.DEQUE_LEN),
                    np.array(np.array(self.gv.data_queue[ch])/7000)),
                    axis=1)

            self.set_plotdata(
                    name=ch, points=pts, color=pg.glColor((ch, 8)), width=1)

    def init_on_off_button(self):
        btn('Start', self.layout, (0, 0), func_conn=self.start,
            max_width=100, min_width=100, color=dark_blue_tab, toggle=True,
            txt_color=white)

    @QtCore.pyqtSlot(bool)
    def start(self, checked):
        if checked:
            self.timer.start(10)
            self.electrod_sphere.timer.start(10)
            self.plane_x.timer.start(10)
            self.plane_y.timer.start(10)
            self.plane_z.timer.start(10)
        else:
            self.timer.stop()
            self.electrod_sphere.timer.stop()
            self.plane_x.timer.stop()
            self.plane_y.timer.start()
            self.plane_z.timer.start()
