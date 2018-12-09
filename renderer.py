import moderngl as mgl
import numpy as np
from pyrr import Matrix44

from base_window import Window, run_window


class Renderer(Window):
    def __init__(self):
        self.ctx = mgl.create_context()

        self.prog = self.ctx.program(
            vertex_shader='''
                #version 330 core

                in vec3 in_vert;
                out float opacity;
                uniform mat4 MVP;
                
                float densityAtRadius(float r){
                    return (132820.15f / (2 * 3.14159f * 3160.0f * 3160.0f)) * exp(-r/3160.0f);
                }
                
                void main(){
                    vec4 v = vec4(in_vert, 1.0);
                    gl_Position = MVP * v;
                    opacity = 1.0f - (densityAtRadius(length(vec2(v))) / densityAtRadius(0.0f));
                }
            ''',
            fragment_shader='''
                #version 330 core

                out vec4 color;
                in float opacity;
                
                void main(){
                    color = vec4(0.3, 0.2, 0.7, opacity);
                }
            ''',
        )

        self.mvp = self.prog['MVP']

        vertices = np.load(file="C:\\temp\\gal.npy")

        self.vbo = self.ctx.buffer(vertices.astype('f4').tobytes())
        self.vao = self.ctx.simple_vertex_array(self.prog, self.vbo, 'in_vert')

        self.zoom = 1.0
        self.last_mouse_down = False
        self.mouse_pos = (0, 0)
        self.theta = (0, 0)

    def handle_mouse(self):
        if self.wnd.wheel > 0:
            self.zoom *= 1.1
        if self.wnd.wheel < 0:
            self.zoom *= 0.9

        if self.wnd.mouse_down:
            if self.last_mouse_down:
                new_theta = (self.theta[0] + (self.wnd.mouse[0] - self.mouse_pos[0]) * 0.05,
                             self.theta[1] + (self.wnd.mouse[1] - self.mouse_pos[1]) * 0.05)
                self.theta = new_theta

        self.mouse_pos = self.wnd.mouse
        self.last_mouse_down = self.wnd.mouse_down

    def render(self):
        self.handle_mouse()

        self.ctx.viewport = self.wnd.viewport
        self.ctx.clear(0.0, 0.0, 0.0)
        self.ctx.enable(mgl.BLEND)

        model = Matrix44.from_scale((self.zoom, self.zoom, self.zoom))
        model *= Matrix44.from_x_rotation(-self.theta[1])
        model *= Matrix44.from_y_rotation(-self.theta[0])
        view = Matrix44.look_at((0.0, 0.0, 1.0), (0.0, 0.0, 0.0), (0.0, 1.0, 0.0))
        projection = Matrix44.perspective_projection(45.0, self.wnd.ratio, 0.1, 100.0)

        self.mvp.write((projection * view * model).astype('f4').tobytes())
        self.vao.render(mode=mgl.POINTS)


run_window(Renderer, out_dir=r"D:\temp\\")
