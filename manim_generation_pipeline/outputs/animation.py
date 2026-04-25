from manim import *

class Scene1_Initialfunctionandstartingpoint(Scene):
    def construct(self):
        plane = NumberPlane(x_range=[-1,4,1], y_range=[-1,4,1], background_line_style={"stroke_opacity": 0.3})
        self.play(Create(plane))
        
        # Draw contour lines for f(x,y) = x^2 + y^2
        contours = VGroup()
        for r in [1, 2, 3, 4]:
            circle = plane.plot_implicit_curve(
                lambda x, y: x**2 + y**2 - r**2,
                color=BLUE,
                stroke_width=2
            )
            contours.add(circle)
        self.play(Create(contours))
        self.wait(1)

        # Initial guess point
        point = Dot(plane.c2p(2, 2), color=YELLOW, radius=0.12)
        label = MathTex(r"(2, 2)").next_to(point, UR, buff=0.1)
        self.play(Create(point), Write(label))
        self.wait(3)

class Scene2_Simplexconstructionwithvertices(Scene):
    def construct(self):
        plane = NumberPlane(x_range=[-1,4,1], y_range=[-1,4,1], background_line_style={"stroke_opacity": 0.3})
        self.add(plane)

        # Vertices
        v1 = Dot(plane.c2p(2, 2), color=RED, radius=0.12)
        v2 = Dot(plane.c2p(2.1, 2), color=GREEN, radius=0.12)
        v3 = Dot(plane.c2p(2, 2.1), color=BLUE, radius=0.12)

        # Lines forming triangle
        l1 = Line(plane.c2p(2, 2), plane.c2p(2.1, 2), color=WHITE)
        l2 = Line(plane.c2p(2.1, 2), plane.c2p(2, 2.1), color=WHITE)
        l3 = Line(plane.c2p(2, 2.1), plane.c2p(2, 2), color=WHITE)

        self.play(Create(v1))
        self.wait(1)
        self.play(Create(v2))
        self.wait(1)
        self.play(Create(v3))
        self.wait(1)

        self.play(Create(l1), Create(l2), Create(l3))
        self.wait(3)

class Scene3_Evaluatefunctionvaluesatvertices(Scene):
    def construct(self):
        plane = NumberPlane(x_range=[-1,4,1], y_range=[-1,4,1], background_line_style={"stroke_opacity": 0.3})
        self.add(plane)

        # Vertices
        v1 = Dot(plane.c2p(2, 2), color=RED, radius=0.12)
        v2 = Dot(plane.c2p(2.1, 2), color=GREEN, radius=0.12)
        v3 = Dot(plane.c2p(2, 2.1), color=BLUE, radius=0.12)
        self.add(v1, v2, v3)

        # Function values
        val1 = Tex("8").next_to(v1, UR, buff=0.1)
        val2 = Tex("8.41").next_to(v2, UR, buff=0.1)
        val3 = Tex("8.41").next_to(v3, UR, buff=0.1)

        # Show calculation for v1
        calc1 = MathTex(r"2^2", r"+", r"2^2", r"=", r"8").to_edge(UP)
        self.play(Write(calc1))
        self.wait(2)
        self.play(FadeOut(calc1))

        # Show calculation for v2
        calc2 = MathTex(r"(2.1)^2", r"+", r"2^2", r"=", r"8.41").to_edge(UP)
        self.play(Write(calc2))
        self.wait(2)
        self.play(FadeOut(calc2))

        # Show calculation for v3
        calc3 = MathTex(r"2^2", r"+", r"(2.1)^2", r"=", r"8.41").to_edge(UP)
        self.play(Write(calc3))
        self.wait(2)
        self.play(FadeOut(calc3))

        self.play(Write(val1), Write(val2), Write(val3))
        self.wait(3)

class Scene4_Sortverticesbyfunctionvalue(Scene):
    def construct(self):
        plane = NumberPlane(x_range=[-1,4,1], y_range=[-1,4,1], background_line_style={"stroke_opacity": 0.3})
        self.add(plane)

        # Original vertices
        v1 = Dot(plane.c2p(2, 2), color=RED, radius=0.12)
        v2 = Dot(plane.c2p(2.1, 2), color=RED, radius=0.12)
        v3 = Dot(plane.c2p(2, 2.1), color=RED, radius=0.12)
        self.add(v1, v2, v3)

        # Values
        val1 = 8
        val2 = 8.41
        val3 = 8.41

        # Sorted positions on right side
        sorted_x = 4
        sorted_y_positions = [2, 1.5, 1]

        # Create sorted dots
        sv1 = Dot(plane.c2p(sorted_x, sorted_y_positions[0]), color=GREEN, radius=0.12)  # lowest value
        sv2 = Dot(plane.c2p(sorted_x, sorted_y_positions[1]), color=RED, radius=0.12)
        sv3 = Dot(plane.c2p(sorted_x, sorted_y_positions[2]), color=RED, radius=0.12)

        # Arrows from original to sorted
        arr1 = Arrow(v1.get_center(), sv1.get_center(), buff=0.1)
        arr2 = Arrow(v2.get_center(), sv2.get_center(), buff=0.1)
        arr3 = Arrow(v3.get_center(), sv3.get_center(), buff=0.1)

        self.play(Create(sv1), Create(sv2), Create(sv3))
        self.wait(1)
        self.play(Create(arr1), Create(arr2), Create(arr3))
        self.wait(3)

class Scene5_Calculatecentroidofbestvertices(Scene):
    def construct(self):
        plane = NumberPlane(x_range=[-1,4,1], y_range=[-1,4,1], background_line_style={"stroke_opacity": 0.3})
        self.add(plane)

        # Best vertices: (2,2) and midpoint of (2.1,2) and (2,2.1)
        v_best1 = Dot(plane.c2p(2, 2), color=GREEN, radius=0.12)
        midpoint_x = (2.1 + 2) / 2
        midpoint_y = (2 + 2.1) / 2
        v_best2 = Dot(plane.c2p(midpoint_x, midpoint_y), color=GREEN, radius=0.12)
        self.add(v_best1, v_best2)

        # Centroid
        centroid_x = (2 + midpoint_x) / 2
        centroid_y = (2 + midpoint_y) / 2
        centroid = Dot(plane.c2p(centroid_x, centroid_y), color=YELLOW, radius=0.12)
        label = MathTex(r"C", color=YELLOW).next_to(centroid, UR, buff=0.1)

        # Dashed lines
        line1 = DashedLine(v_best1.get_center(), centroid.get_center(), color=YELLOW)
        line2 = DashedLine(v_best2.get_center(), centroid.get_center(), color=YELLOW)

        self.play(Create(v_best1), Create(v_best2))
        self.wait(1)
        self.play(Create(centroid), Write(label))
        self.wait(1)
        self.play(Create(line1), Create(line2))
        self.wait(3)

class Scene6_Reflectworstvertexacrosscentroid(Scene):
    def construct(self):
        plane = NumberPlane(x_range=[-1,4,1], y_range=[-1,4,1], background_line_style={"stroke_opacity": 0.3})
        self.add(plane)

        # Worst vertex (2.1, 2)
        worst = Dot(plane.c2p(2.1, 2), color=RED, radius=0.12)
        # Centroid (2.0333, 2.0333)
        centroid = Dot(plane.c2p(2.0333, 2.0333), color=YELLOW, radius=0.12)
        self.add(worst, centroid)

        # Calculate reflected point
        wx, wy = 2.1, 2
        cx, cy = 2.0333, 2.0333
        rx = 2 * cx - wx
        ry = 2 * cy - wy
        reflected = Dot(plane.c2p(rx, ry), color=GREEN, radius=0.12)

        # Arrow from worst through centroid to reflected
        arrow = Arrow(worst.get_center(), reflected.get_center(), buff=0.1, color=GREEN)

        self.play(Create(worst), Create(centroid))
        self.wait(1)
        self.play(Create(arrow))
        self.wait(1)
        self.play(Create(reflected))
        self.wait(3)

class Scene7_Expansionifreflectedpointisbetter(Scene):
    def construct(self):
        plane = NumberPlane(x_range=[-1,4,1], y_range=[-1,4,1], background_line_style={"stroke_opacity": 0.3})
        self.add(plane)

        centroid = plane.c2p(2.0333, 2.0333)
        reflected = plane.c2p(1.9666, 2.0666)  # from previous reflection

        # Expanded point further along line from centroid through reflected
        vector = reflected - centroid
        expanded_point = centroid + 1.5 * vector

        dot_reflected = Dot(reflected, color=GREEN, radius=0.12)
        dot_expanded = Dot(expanded_point, color=ORANGE, radius=0.12)

        arrow = Arrow(centroid, expanded_point, buff=0.1, color=ORANGE)

        self.play(Create(dot_reflected), Create(Dot(centroid, color=YELLOW, radius=0.12)))
        self.wait(1)
        self.play(Create(arrow))
        self.wait(1)
        self.play(Create(dot_expanded))
        self.wait(3)

class Scene8_Contractionifreflectedpointisworse(Scene):
    def construct(self):
        plane = NumberPlane(x_range=[-1,4,1], y_range=[-1,4,1], background_line_style={"stroke_opacity": 0.3})
        self.add(plane)

        centroid = plane.c2p(2.0333, 2.0333)
        reflected = plane.c2p(1.9666, 2.0666)

        # Contracted point closer to centroid from reflected
        vector = reflected - centroid
        contracted_point = centroid + 0.5 * vector

        dot_reflected = Dot(reflected, color=GREEN, radius=0.12)
        dot_contracted = Dot(contracted_point, color=PURPLE, radius=0.12)

        arrow = Arrow(reflected, centroid, buff=0.1, color=PURPLE)

        self.play(Create(dot_reflected), Create(Dot(centroid, color=YELLOW, radius=0.12)))
        self.wait(1)
        self.play(Create(arrow))
        self.wait(1)
        self.play(Create(dot_contracted))
        self.wait(3)

class Scene9_Iterationandconvergencetominimum(Scene):
    def construct(self):
        plane = NumberPlane(x_range=[-1,4,1], y_range=[-1,4,1], background_line_style={"stroke_opacity": 0.3})
        self.add(plane)

        # Contour lines
        contours = VGroup()
        for r in [3, 2, 1, 0.5, 0.2]:
            circle = plane.plot_implicit_curve(
                lambda x, y: x**2 + y**2 - r**2,
                color=BLUE,
                stroke_width=2
            )
            contours.add(circle)
        self.add(contours)

        # Initial simplex vertices
        vertices = [np.array([2, 2, 0]), np.array([2.1, 2, 0]), np.array([2, 2.1, 0])]
        dots = [Dot(plane.c2p(*v[:2]), color=RED, radius=0.12) for v in vertices]
        self.add(*dots)

        # Animate shrinking and moving towards origin
        for i in range(5):
            new_vertices = [v * 0.6 for v in vertices]
            new_dots = [Dot(plane.c2p(*v[:2]), color=RED, radius=0.12) for v in new_vertices]
            anims = [Transform(dots[j], new_dots[j]) for j in range(3)]
            self.play(*anims)
            vertices = new_vertices
            dots = new_dots
            self.wait(0.5)

        # Highlight final minimum point at origin
        minimum = Dot(plane.c2p(0, 0), color=YELLOW, radius=0.15)
        label = MathTex(r"(0, 0)", color=YELLOW).next_to(minimum, UR, buff=0.1)
        self.play(Create(minimum), Write(label))
        self.wait(3)