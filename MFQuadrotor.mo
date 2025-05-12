package GSQuad
  package Components
    model Quadrotor
    
      // note: this is a multi-fidelity quadrotor model
      // load packages
      import GSQuad.Constants;
      import GSQuad.Utils.quat2eul;
      
      // setup fidelity level and load different fidelity quadrotor model
      parameter Integer fidelity = 1;
      QuadLowFidelity quad_low if fidelity == 1;
      
      // parameters
      parameter Real pwm_interval = 0.01 if fidelity == 1;          // [sec] PWM signal frequency
      parameter Real sample_interval = 0.01 if fidelity == 1;       // [sec] sensing frequency
      parameter Real pwm_min = 1000;
      parameter Real pwm_max = 2000;
      
      // input: four PWM inputs for rotors
      // channel 1: Right-up (omega_min:1000, omega_max:2000)
      // channel 2: Right-down (omega_min:1000, omega_max:2000)
      // channel 3: Left-down (omega_min:1000, omega_max:2000)
      // channel 4: Left-up (omega_min:1000, omega_max:2000)
      Connectors.ControlBus control annotation(
        Placement(transformation(origin = {-120, 7}, extent = {{-19.8, -12.375}, {19.8, 12.375}}), iconTransformation(origin = {-129.4, 21.125}, extent = {{-28.6, -17.875}, {28.6, 17.875}})));
      Connectors.RealInput pwm_rotor_cmd[4];
      
      // output
      Connectors.SensorBus sensor annotation(
        Placement(transformation(origin = {120, 7}, extent = {{-19.8, -12.375}, {19.8, 12.375}}), iconTransformation(origin = {129.6, 21.75}, extent = {{-27.6, -17.25}, {27.6, 17.25}})));
      Connectors.RealOutput pos_op_w_meas[3], vel_w_p_b_meas[3], quat_wb_meas[4], omega_wb_b_meas[3];
      Connectors.RealOutput acc_w_p_b_meas[3], euler_wb_meas[3];
      
      // internal states
      Real acc_w_p_b[3], euler_wb[3];           // [m/s^2, rad] acceleration of p(cg) in world frame(w) expressed in body frame(b), euler angle from world(w) to body(b)
    
    equation
    
      connect(control.pwm_1, pwm_rotor_cmd[1]);
      connect(control.pwm_2, pwm_rotor_cmd[2]);
      connect(control.pwm_3, pwm_rotor_cmd[3]);
      connect(control.pwm_4, pwm_rotor_cmd[4]);
    
      connect(sensor.x_op_w, pos_op_w_meas[1]);
      connect(sensor.y_op_w, pos_op_w_meas[2]);
      connect(sensor.z_op_w, pos_op_w_meas[3]);
      connect(sensor.u_w_p_b, vel_w_p_b_meas[1]);
      connect(sensor.v_w_p_b, vel_w_p_b_meas[2]);
      connect(sensor.w_w_p_b, vel_w_p_b_meas[3]);
      connect(sensor.ax_w_p_b_meas, acc_w_p_b_meas[1]);
      connect(sensor.ay_w_p_b_meas, acc_w_p_b_meas[2]);
      connect(sensor.az_w_p_b_meas, acc_w_p_b_meas[3]);
      connect(sensor.q0_wb, quat_wb_meas[1]);
      connect(sensor.q1_wb, quat_wb_meas[2]);
      connect(sensor.q2_wb, quat_wb_meas[3]);
      connect(sensor.q3_wb, quat_wb_meas[4]);
      connect(sensor.phi_wb, euler_wb_meas[1]);
      connect(sensor.theta_wb, euler_wb_meas[2]);
      connect(sensor.psi_wb, euler_wb_meas[3]);
      connect(sensor.p_wb_b, omega_wb_b_meas[1]);
      connect(sensor.q_wb_b, omega_wb_b_meas[2]);
      connect(sensor.r_wb_b, omega_wb_b_meas[3]);

      // equation for sensor sampling
      if fidelity == 1 then
        euler_wb = quat2eul(quad_low.quaternion_wb);
        acc_w_p_b = {0.0,0.0,0.0};
      end if;
      
      when sample(0, sample_interval) then
      
        if fidelity == 1 then    
          pos_op_w_meas = quad_low.position_op_w;
          vel_w_p_b_meas = quad_low.velocity_w_p_b;
          quat_wb_meas = quad_low.quaternion_wb;
          omega_wb_b_meas = quad_low.omega_wb_b;
          acc_w_p_b_meas = acc_w_p_b;
          euler_wb_meas[1] = euler_wb[1];
          euler_wb_meas[2] = euler_wb[2];
          euler_wb_meas[3] = mod(euler_wb[3]+Constants.pi,2*Constants.pi)-Constants.pi;
    
        end if;
        
      end when;
      
    algorithm
    
      // algorithm for pwm sampling of ESC/servo
      when sample(0, pwm_interval) then
      
        if fidelity == 1 then
          for idx in 1:4 loop
            quad_low.omega_rotor_cmd[idx] := (quad_low.omega_rotor_max-quad_low.omega_rotor_min)*(pwm_rotor_cmd[idx]-pwm_min)/(pwm_max-pwm_min)+quad_low.omega_rotor_min;
          end for;
        end if;
        
      end when;
    
    annotation(
        Icon(graphics = {Ellipse(origin = {-70, 70}, extent = {{-30, 30}, {30, -30}}), Ellipse(origin = {70, 70}, extent = {{-30, 30}, {30, -30}}), Ellipse(origin = {-70, -70}, extent = {{-30, 30}, {30, -30}}), Ellipse(origin = {70, -70}, extent = {{-30, 30}, {30, -30}}), Polygon(points = {{-20, 40}, {-40, 20}, {-40, -20}, {-20, -40}, {20, -40}, {40, -20}, {40, 20}, {20, 40}, {0, 40}, {-20, 40}}), Ellipse(origin = {-70, 70}, fillPattern = FillPattern.Solid, extent = {{-2, 2}, {2, -2}}), Polygon(origin = {-48, 48}, points = {{-22, 22}, {14, -22}, {20, -16}, {22, -14}, {-22, 22}, {-22, 22}}), Polygon(origin = {48, 48}, points = {{22, 22}, {-14, -22}, {-22, -14}, {22, 22}, {22, 22}}), Ellipse(origin = {70, -70}, fillPattern = FillPattern.Solid, extent = {{-2, 2}, {2, -2}}), Ellipse(origin = {70, 70}, fillPattern = FillPattern.Solid, extent = {{-2, 2}, {2, -2}}), Polygon(origin = {48, -48}, points = {{22, -22}, {-14, 22}, {-22, 14}, {22, -22}, {22, -22}}), Ellipse(origin = {-70, -70}, fillPattern = FillPattern.Solid, extent = {{-2, 2}, {2, -2}}), Polygon(origin = {-48, -48}, points = {{-22, -22}, {22, 14}, {14, 22}, {-22, -22}, {-22, -22}}), Ellipse(origin = {70, 54}, extent = {{-2, -14}, {2, 14}}), Ellipse(origin = {70, 86}, extent = {{-2, -14}, {2, 14}}), Ellipse(origin = {-70, 86}, extent = {{-2, -14}, {2, 14}}), Ellipse(origin = {-70, 54}, extent = {{-2, -14}, {2, 14}}), Ellipse(origin = {-70, -54}, extent = {{-2, -14}, {2, 14}}), Ellipse(origin = {-70, -86}, extent = {{-2, -14}, {2, 14}}), Ellipse(origin = {70, -54}, extent = {{-2, -14}, {2, 14}}), Ellipse(origin = {70, -86}, extent = {{-2, -14}, {2, 14}})}));
        
    end Quadrotor;

    model Controller
      // input, sensor signal
      Connectors.SensorBus sensor annotation(
        Placement(transformation(origin = {120.2, 6.375}, extent = {{-20.2, -12.625}, {20.2, 12.625}}), iconTransformation(origin = {133, 0.875}, extent = {{-29, -18.125}, {29, 18.25}})));
      //Connectors.RealInput pos_op_w_fdbk[3], vel_w_p_b_fdbk[3], quat_wb_fdbk[4], omega_wb_b_fdbk[3];
      
      // output, control singal (pwm)
      Connectors.ControlBus control annotation(
        Placement(transformation(origin = {-120.2, 6.375}, extent = {{-20.2, -12.625}, {20.2, 12.625}}), iconTransformation(origin = {-133, 0.875}, extent = {{-29, -18.125}, {29, 18.125}})));
      Connectors.IntegerOutput pwm_rotor_cmd[4];
    
    equation
     
      //connect(sensor.AAA, AAA);
     
      connect(control.pwm_1, pwm_rotor_cmd[1]);
      connect(control.pwm_2, pwm_rotor_cmd[2]);
      connect(control.pwm_3, pwm_rotor_cmd[3]);
      connect(control.pwm_4, pwm_rotor_cmd[4]);

    algorithm
// algorithm models pwm sampling of ESC/servo
      when sample(0, 0.01) then
      
        pwm_rotor_cmd := {0, 0, 0, 0};
        
      end when;
    
      annotation(
        Diagram,
        Icon(graphics = {Rectangle(origin = {0, -14}, fillPattern = FillPattern.Solid, extent = {{-20, 30}, {20, -30}}), Rectangle(origin = {25, 11}, fillPattern = FillPattern.Solid, extent = {{-5, 1}, {5, -1}}), Rectangle(origin = {25, -5}, fillPattern = FillPattern.Solid, extent = {{-5, 1}, {5, -1}}), Rectangle(origin = {25, 3}, fillPattern = FillPattern.Solid, extent = {{-5, 1}, {5, -1}}), Rectangle(origin = {25, -13}, fillPattern = FillPattern.Solid, extent = {{-5, 1}, {5, -1}}), Rectangle(origin = {25, -21}, fillPattern = FillPattern.Solid, extent = {{-5, 1}, {5, -1}}), Rectangle(origin = {-25, 11}, fillPattern = FillPattern.Solid, extent = {{-5, 1}, {5, -1}}), Rectangle(origin = {-25, 3}, fillPattern = FillPattern.Solid, extent = {{-5, 1}, {5, -1}}), Rectangle(origin = {-25, -5}, fillPattern = FillPattern.Solid, extent = {{-5, 1}, {5, -1}}), Rectangle(origin = {-25, -13}, fillPattern = FillPattern.Solid, extent = {{-5, 1}, {5, -1}}), Rectangle(origin = {-25, -21}, fillPattern = FillPattern.Solid, extent = {{-5, 1}, {5, -1}}), Rectangle(lineThickness = 0.75, extent = {{-60, 80}, {60, -80}}), Rectangle(origin = {28, -59}, lineThickness = 1.25, extent = {{-20, 5}, {20, -5}}), Rectangle(origin = {-44, 61}, lineThickness = 0.5, extent = {{-10, 5}, {10, -5}}), Rectangle(origin = {28, -59}, fillPattern = FillPattern.Solid, extent = {{-10, 1}, {10, -1}}), Rectangle(origin = {-28, -59}, lineThickness = 1.25, extent = {{-20, 5}, {20, -5}}), Rectangle(origin = {-28, -59}, fillPattern = FillPattern.Solid, extent = {{-10, 1}, {10, -1}}), Rectangle(origin = {-44, 58}, lineThickness = 0.5, extent = {{-6, 2}, {6, -2}}), Rectangle(origin = {-52, 57}, fillPattern = FillPattern.Solid, extent = {{-2, 1}, {2, -1}}), Rectangle(origin = {-36, 57}, fillPattern = FillPattern.Solid, extent = {{-2, 1}, {2, -1}}), Rectangle(origin = {-51, 63}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {-47, 63}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {-41, 63}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {-37, 63}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {-44, 45}, lineThickness = 0.5, extent = {{-10, 5}, {10, -5}}), Rectangle(origin = {-44, 42}, lineThickness = 0.5, extent = {{-6, 2}, {6, -2}}), Rectangle(origin = {-52, 41}, fillPattern = FillPattern.Solid, extent = {{-2, 1}, {2, -1}}), Rectangle(origin = {-36, 41}, fillPattern = FillPattern.Solid, extent = {{-2, 1}, {2, -1}}), Rectangle(origin = {-51, 47}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {-47, 47}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {-41, 47}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {-37, 47}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {16, 61}, lineThickness = 0.5, extent = {{-10, 5}, {10, -5}}), Rectangle(origin = {16, 58}, lineThickness = 0.5, extent = {{-6, 2}, {6, -2}}), Rectangle(origin = {8, 57}, fillPattern = FillPattern.Solid, extent = {{-2, 1}, {2, -1}}), Rectangle(origin = {24, 57}, fillPattern = FillPattern.Solid, extent = {{-2, 1}, {2, -1}}), Rectangle(origin = {9, 63}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {13, 63}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {19, 63}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {23, 63}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {-16, 61}, lineThickness = 0.5, extent = {{-10, 5}, {10, -5}}), Rectangle(origin = {-16, 58}, lineThickness = 0.5, extent = {{-6, 2}, {6, -2}}), Rectangle(origin = {-24, 57}, fillPattern = FillPattern.Solid, extent = {{-2, 1}, {2, -1}}), Rectangle(origin = {-8, 57}, fillPattern = FillPattern.Solid, extent = {{-2, 1}, {2, -1}}), Rectangle(origin = {-23, 63}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {-19, 63}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {-13, 63}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {-9, 63}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {44, 45}, lineThickness = 0.5, extent = {{-10, 5}, {10, -5}}), Rectangle(origin = {44, 42}, lineThickness = 0.5, extent = {{-6, 2}, {6, -2}}), Rectangle(origin = {36, 41}, fillPattern = FillPattern.Solid, extent = {{-2, 1}, {2, -1}}), Rectangle(origin = {52, 41}, fillPattern = FillPattern.Solid, extent = {{-2, 1}, {2, -1}}), Rectangle(origin = {37, 47}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {41, 47}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {47, 47}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {51, 47}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {44, 61}, lineThickness = 0.5, extent = {{-10, 5}, {10, -5}}), Rectangle(origin = {44, 58}, lineThickness = 0.5, extent = {{-6, 2}, {6, -2}}), Rectangle(origin = {36, 57}, fillPattern = FillPattern.Solid, extent = {{-2, 1}, {2, -1}}), Rectangle(origin = {52, 57}, fillPattern = FillPattern.Solid, extent = {{-2, 1}, {2, -1}}), Rectangle(origin = {37, 63}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {41, 63}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {47, 63}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {51, 63}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {-13, 44}, lineThickness = 0.5, extent = {{-7, 4}, {7, -4}}), Rectangle(origin = {-17, 45}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {-9, 45}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {-13, 45}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {13, 44}, lineThickness = 0.5, extent = {{-7, 4}, {7, -4}}), Rectangle(origin = {9, 45}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {17, 45}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {13, 45}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Ellipse(origin = {-55, 75}, lineThickness = 0.5, extent = {{-3, 3}, {3, -3}}), Line(origin = {-55, 75}, points = {{-1, 1}, {1, -1}, {1, -1}}), Rectangle(origin = {-25, 29}, lineThickness = 0.5, extent = {{-15, 5}, {15, -5}}), Rectangle(origin = {-25, 26}, lineThickness = 0.5, extent = {{-11, 2}, {11, -2}}), Rectangle(origin = {-37, 31}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {-33, 31}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {-29, 31}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {-25, 31}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {-21, 31}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {-17, 31}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {-13, 31}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {25, 29}, lineThickness = 0.5, extent = {{-15, 5}, {15, -5}}), Rectangle(origin = {25, 26}, lineThickness = 0.5, extent = {{-11, 2}, {11, -2}}), Rectangle(origin = {13, 31}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {17, 31}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {21, 31}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {25, 31}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {29, 31}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {33, 31}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Rectangle(origin = {37, 31}, lineThickness = 0.5, extent = {{-1, 1}, {1, -1}}), Line(origin = {-55, 75}, points = {{1, 1}, {-1, -1}, {-1, -1}}), Ellipse(origin = {-55, 75}, lineThickness = 0.5, extent = {{-3, 3}, {3, -3}}), Line(origin = {-55, 75}, points = {{-1, 1}, {1, -1}, {1, -1}}), Line(origin = {-55, 75}, points = {{1, 1}, {-1, -1}, {-1, -1}}), Ellipse(origin = {55, 75}, lineThickness = 0.5, extent = {{-3, 3}, {3, -3}}), Line(origin = {55, 75}, points = {{-1, 1}, {1, -1}, {1, -1}}), Line(origin = {55, 75}, points = {{1, 1}, {-1, -1}, {-1, -1}}), Ellipse(origin = {55, 75}, lineThickness = 0.5, extent = {{-3, 3}, {3, -3}}), Line(origin = {55, 75}, points = {{-1, 1}, {1, -1}, {1, -1}}), Line(origin = {55, 75}, points = {{1, 1}, {-1, -1}, {-1, -1}}), Ellipse(origin = {-55, -75}, lineThickness = 0.5, extent = {{-3, 3}, {3, -3}}), Line(origin = {-55, -75}, points = {{-1, 1}, {1, -1}, {1, -1}}), Line(origin = {-55, -75}, points = {{1, 1}, {-1, -1}, {-1, -1}}), Ellipse(origin = {-55, -75}, lineThickness = 0.5, extent = {{-3, 3}, {3, -3}}), Line(origin = {-55, -75}, points = {{-1, 1}, {1, -1}, {1, -1}}), Line(origin = {-55, -75}, points = {{1, 1}, {-1, -1}, {-1, -1}}), Ellipse(origin = {55, -75}, lineThickness = 0.5, extent = {{-3, 3}, {3, -3}}), Line(origin = {55, -75}, points = {{-1, 1}, {1, -1}, {1, -1}}), Line(origin = {55, -75}, points = {{1, 1}, {-1, -1}, {-1, -1}}), Ellipse(origin = {55, -75}, lineThickness = 0.5, extent = {{-3, 3}, {3, -3}}), Line(origin = {55, -75}, points = {{-1, 1}, {1, -1}, {1, -1}}), Line(origin = {55, -75}, points = {{1, 1}, {-1, -1}, {-1, -1}}), Rectangle(origin = {-25, -29}, fillPattern = FillPattern.Solid, extent = {{-5, 1}, {5, -1}}), Rectangle(origin = {-25, -37}, fillPattern = FillPattern.Solid, extent = {{-5, 1}, {5, -1}}), Rectangle(origin = {25, -29}, fillPattern = FillPattern.Solid, extent = {{-5, 1}, {5, -1}}), Rectangle(origin = {25, -37}, fillPattern = FillPattern.Solid, extent = {{-5, 1}, {5, -1}})}));
    
    end Controller;

    model QuadLowFidelity
      
      // note: this is a low-fidelity quadrotor model, considering quadrotor dynamics only (w/o aerodynamic, motor, sensor dynamics)
      // load packages
      import GSQuad.Constants;
      import GSQuad.Utils.clip;
      import GSQuad.Utils.quat2rot;
      import GSQuad.Utils.hatmap;
      import Modelica.Math.Matrices.inv;
      
      // parameters
      parameter Real mass = 0.500;      // [kg] mass of quadrotor
      parameter Real Ixx = 3.65e-3;     // [kg*m^2] x moment of inertia
      parameter Real Iyy = 3.68e-3;     // [kg*m^2] y moment of inertia
      parameter Real Izz = 7.03e-3;     // [kg*m^2] z moment of inertia
      parameter Real Ixy = 0.0;         // [kg*m^2] xy product inertia
      parameter Real Iyz = 0.0;         // [kg*m^2] yz product inertia
      parameter Real Ixz = 0.0;         // [kg*m^2] xz product inertia
      parameter Real Ir = 0.0;                // [kg*m^2] rotor inertia
      parameter Real d_arm = 0.17;      // [m] arm length from cg to each rotor
      parameter Real rotor_pos[3, 4] = d_arm*[cos(45/180*Constants.pi), cos(135/180*Constants.pi), cos(225/180*Constants.pi), cos(315/180*Constants.pi); sin(45/180*Constants.pi), sin(135/180*Constants.pi), sin(225/180*Constants.pi), sin(315/180*Constants.pi); 0.0, 0.0, 0.0, 0.0];  // [m] rotor position w.r.t cg
      parameter Integer rotor_dir[4] = {1, -1, 1, -1};        // [-] rotating direction of rotors (+1: CCW, -1: CW, CCW rotation = CW torque = +Z yaw moment)
      parameter Real k_eta = 5.570e-6;        // [N/(rad/s)^2] thrust coefficient
      parameter Real k_m = 0.136e-6;          // [N*m/(rad/s)^2] yaw moment coefficient
      parameter Real omega_rotor_max = 1500;  // [rad/s] rotor maximum rotational speed
      parameter Real omega_rotor_min = 0;     // [rad/s] rotor minimum rotational speed
      parameter Real quat_fdbk_correction = 0.1;          // [-] feedback correction term for quaternion (numerical constraints as lagrange multiplier)
      
      // inputs
      discrete Real omega_rotor_cmd[4];       // [rad/s] rotational speed command from ESC
      
      // states
      Real position_op_w[3](start = {0, 0, 0}, each fixed = false);     // [m] position of p(cg) vector from origin o in world frame(w) = ned position from origin
      Real velocity_w_p_b[3](start = {0, 0, 0}, each fixed = false);    // [m/s] velocity of p(cg) in world frame(w) expressed in body frame(b) = body velocity
      Real quaternion_wb[4](start = {1, 0, 0, 0}, each fixed = false);  // [-] attitude of body frame(b) relative to world frame(w) = attitude w.r.t ned
      Real omega_wb_b[3](start = {0, 0, 0}, each fixed = false);        // [rad/s] rate of body frame(b) relative to world frame(w) expressed in body frame(b) = p,q,r
      Real omega_motor[4](start = {0, 0, 0, 0}, each fixed = false);    // [rad/s] rotational speed of rotors
      
      // internal states
      Real F_b[3], M_b[3];                    // [N, N*m] force/moment in body coordinates
      Real J[3,3], R[3,3], Omega[4,4];        // [-] inertia, rotation, quaternion kinematic matrix

    equation
    
      // compute body forces and moments
      for idx in 1:4 loop
        omega_motor[idx] = clip(omega_rotor_cmd[idx], omega_rotor_min, omega_rotor_max);
      end for;
      F_b = sum({0, 0, -k_eta*omega_motor[idx]^2} for idx in 1:4);
      M_b = sum(cross(rotor_pos[:, idx],{0, 0, -k_eta*omega_motor[idx]^2})+(rotor_dir[idx]*{0, 0, k_m*omega_motor[idx]^2}) for idx in 1:4);

      // compute coordinate transformation matrix from w to b
      R = transpose(quat2rot(quaternion_wb));

      // get inertia matrix
      J = [Ixx, Ixy, Ixz; Ixy, Iyy, Iyz; Ixz, Iyz, Izz];

      // compute quaternion kinematic matrix
      Omega = [0.0, -omega_wb_b[1], -omega_wb_b[2], -omega_wb_b[3]; omega_wb_b[1], 0.0, omega_wb_b[3], -omega_wb_b[2]; omega_wb_b[2], -omega_wb_b[3], 0.0, omega_wb_b[1]; omega_wb_b[3], omega_wb_b[2], -omega_wb_b[1], 0.0];

      // compute the derivative
      der(position_op_w) = transpose(R)*velocity_w_p_b;
      der(velocity_w_p_b) = -cross(omega_wb_b, velocity_w_p_b) + 1/mass*F_b + R*{0, 0, Constants.g};
      der(quaternion_wb) = 0.5*Omega*quaternion_wb + quat_fdbk_correction*(1-sum(quaternion_wb.*quaternion_wb))*quaternion_wb;
      der(omega_wb_b) = inv(J)*(-hatmap({omega_wb_b[1], omega_wb_b[2], omega_wb_b[3]})*(J*{omega_wb_b[1], omega_wb_b[2], omega_wb_b[3]}) + M_b);
      
    end QuadLowFidelity;
  end Components;

  package Connectors
    connector IntegerInput = input Integer "'input Integer' as connector" annotation(
      defaultComponentName = "u",
      Icon(graphics = {Polygon(lineColor = {255, 127, 0}, fillColor = {255, 127, 0}, fillPattern = FillPattern.Solid, points = {{-100, 100}, {100, 0}, {-100, -100}, {-100, 100}}), Text(origin = {0, -120}, extent = {{-100, 20}, {100, -20}}, textString = "%name")}, coordinateSystem(extent = {{-100, 100}, {100, -140}}, preserveAspectRatio = true, initialScale = 0.2)),
      Diagram(coordinateSystem(preserveAspectRatio = true, initialScale = 0.2, extent = {{-100, -100}, {100, 100}}), graphics = {Polygon(points = {{0, 50}, {100, 0}, {0, -50}, {0, 50}}, lineColor = {255, 127, 0}, fillColor = {255, 127, 0}, fillPattern = FillPattern.Solid), Text(extent = {{-10, 85}, {-10, 60}}, textColor = {255, 127, 0}, textString = "%name")}),
      Documentation(info = "<html>
  <p>
  Connector with one input signal of type Integer.
  </p>
  </html>"));
    connector IntegerOutput = output Integer "'output Integer' as connector" annotation(
      defaultComponentName = "y",
      Icon(coordinateSystem(preserveAspectRatio = true, extent = {{-100, 100}, {100, -100}}), graphics = {Polygon(lineColor = {255, 127, 0}, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid, points = {{-100, 100}, {100, 0}, {-100, -100}, {-100, 100}}), Text(origin = {0, -120}, extent = {{-100, 20}, {100, -20}}, textString = "%name")}),
      Diagram(coordinateSystem(preserveAspectRatio = true, extent = {{-100, -100}, {100, 100}}), graphics = {Polygon(points = {{-100, 50}, {0, 0}, {-100, -50}, {-100, 50}}, lineColor = {255, 127, 0}, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid), Text(extent = {{30, 110}, {30, 60}}, textColor = {255, 127, 0}, textString = "%name")}),
      Documentation(info = "<html>
    <p>
    Connector with one output signal of type Integer.
    </p>
    </html>"));
    connector RealOutput = output Real "'output Real' as connector" annotation(
      defaultComponentName = "y",
      Icon(coordinateSystem(preserveAspectRatio = true, extent = {{-100, -100}, {100, 100}}), graphics = {Polygon(lineColor = {0, 0, 127}, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid, points = {{-100, 100}, {100, 0}, {-100, -100}, {-100, 100}}), Text(origin = {0, -121}, extent = {{-98, 19}, {98, -19}}, textString = "%name")}),
      Diagram(coordinateSystem(preserveAspectRatio = true, extent = {{-100.0, -100.0}, {100.0, 100.0}}), graphics = {Polygon(lineColor = {0, 0, 127}, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid, points = {{-100.0, 50.0}, {0.0, 0.0}, {-100.0, -50.0}}), Text(textColor = {0, 0, 127}, extent = {{30.0, 60.0}, {30.0, 110.0}}, textString = "%name")}),
      Documentation(info = "<html>
    <p>
    Connector with one output signal of type Real.
    </p>
    </html>"));
    connector RealInput = input Real "'input Real' as connector" annotation(
      defaultComponentName = "u",
      Icon(graphics = {Polygon(lineColor = {0, 0, 127}, fillColor = {0, 0, 127}, fillPattern = FillPattern.Solid, points = {{-100, 100}, {100, 0}, {-100, -100}, {-100, 100}}), Text(origin = {-1, -120}, extent = {{-101, 20}, {101, -20}}, textString = "%name")}, coordinateSystem(extent = {{-100, -100}, {100, 100}}, preserveAspectRatio = true, initialScale = 0.2)),
      Diagram(coordinateSystem(preserveAspectRatio = true, initialScale = 0.2, extent = {{-100.0, -100.0}, {100.0, 100.0}}), graphics = {Polygon(lineColor = {0, 0, 127}, fillColor = {0, 0, 127}, fillPattern = FillPattern.Solid, points = {{0.0, 50.0}, {100.0, 0.0}, {0.0, -50.0}, {0.0, 50.0}}), Text(textColor = {0, 0, 127}, extent = {{-10.0, 60.0}, {-10.0, 85.0}}, textString = "%name")}),
      Documentation(info = "<html>
    <p>
    Connector with one input signal of type Real.
    </p>
    </html>"));

    expandable connector ControlBus
      annotation(
        Icon(graphics = {Polygon(origin = {0, -20}, points = {{-50, -20}, {-80, 40}, {80, 40}, {50, -20}, {-50, -20}}), Ellipse(origin = {17, 0}, extent = {{-9, 8}, {9, -8}}), Ellipse(origin = {-19, 0}, extent = {{-9, 8}, {9, -8}}), Ellipse(origin = {-51, 0}, extent = {{-9, 8}, {9, -8}}), Ellipse(origin = {49, 0}, extent = {{-9, 8}, {9, -8}}), Ellipse(origin = {-31, -24}, extent = {{-9, 8}, {9, -8}}), Ellipse(origin = {-1, -24}, extent = {{-9, 8}, {9, -8}}), Ellipse(origin = {29, -24}, extent = {{-9, 8}, {9, -8}}), Text(origin = {0, -60}, extent = {{-80, 20}, {80, -20}}, textString = "%name")}, coordinateSystem(extent = {{-80, 20}, {80, -80}})),
        Diagram(graphics = {Polygon(origin = {0, -20}, points = {{-50, -20}, {-80, 40}, {80, 40}, {50, -20}, {-50, -20}}), Ellipse(origin = {17, 0}, extent = {{-9, 8}, {9, -8}}), Ellipse(origin = {-19, 0}, extent = {{-9, 8}, {9, -8}}), Ellipse(origin = {-51, 0}, extent = {{-9, 8}, {9, -8}}), Ellipse(origin = {49, 0}, extent = {{-9, 8}, {9, -8}}), Ellipse(origin = {-31, -24}, extent = {{-9, 8}, {9, -8}}), Ellipse(origin = {-1, -24}, extent = {{-9, 8}, {9, -8}}), Ellipse(origin = {29, -24}, extent = {{-9, 8}, {9, -8}}), Text(origin = {0, -60}, extent = {{-80, 20}, {80, -20}}, textString = "%name")}, coordinateSystem(extent = {{-80, 20}, {80, -80}})));
    end ControlBus;

    expandable connector SensorBus
      annotation(
        Icon(graphics = {Polygon(origin = {0, -20}, points = {{-50, -20}, {-80, 40}, {80, 40}, {50, -20}, {-50, -20}}), Ellipse(origin = {17, 0}, extent = {{-9, 8}, {9, -8}}), Ellipse(origin = {-19, 0}, extent = {{-9, 8}, {9, -8}}), Ellipse(origin = {-51, 0}, extent = {{-9, 8}, {9, -8}}), Ellipse(origin = {49, 0}, extent = {{-9, 8}, {9, -8}}), Ellipse(origin = {-31, -24}, extent = {{-9, 8}, {9, -8}}), Ellipse(origin = {-1, -24}, extent = {{-9, 8}, {9, -8}}), Ellipse(origin = {29, -24}, extent = {{-9, 8}, {9, -8}}), Text(origin = {0, -60}, extent = {{-80, 20}, {80, -20}}, textString = "%name")}, coordinateSystem(extent = {{-80, 20}, {80, -80}})),
        Diagram(graphics = {Polygon(origin = {0, -20}, points = {{-50, -20}, {-80, 40}, {80, 40}, {50, -20}, {-50, -20}}), Ellipse(origin = {17, 0}, extent = {{-9, 8}, {9, -8}}), Ellipse(origin = {-19, 0}, extent = {{-9, 8}, {9, -8}}), Ellipse(origin = {-51, 0}, extent = {{-9, 8}, {9, -8}}), Ellipse(origin = {49, 0}, extent = {{-9, 8}, {9, -8}}), Ellipse(origin = {-31, -24}, extent = {{-9, 8}, {9, -8}}), Ellipse(origin = {-1, -24}, extent = {{-9, 8}, {9, -8}}), Ellipse(origin = {29, -24}, extent = {{-9, 8}, {9, -8}}), Text(origin = {0, -60}, extent = {{-80, 20}, {80, -20}}, textString = "%name")}, coordinateSystem(extent = {{-80, 20}, {80, -80}})));
    end SensorBus;


  end Connectors;

  package Constants
    constant Real pi = 3.14159265;
    constant Real g = 9.80665;
    constant Real eps = 1.0e-15;
    constant Real r2d = 180/pi;
    constant Real d2r = pi/180;
    constant Real rpm2radps = 2*pi/60;
    constant Real radps2rpm = 60/2/pi;
  end Constants;

  package Utils
    function quat2rot
      // note: this is a function for conversion between quaternion and rotational matrix (SO3, dcm)
      //       resulting matrix is not coordinate transformation matrix, rotation matrix (take transpose for coordinate transform)
      // input
      input Real q[4];
      // [-] quaternion
      // output
      output Real R[3, 3];
      // [-] rotation matrix
    algorithm
      R[1, 1] := q[1]*q[1] + q[2]*q[2] - q[3]*q[3] - q[4]*q[4];
      R[1, 2] := 2*(q[2]*q[3] - q[1]*q[4]);
      R[1, 3] := 2*(q[2]*q[4] + q[1]*q[3]);
      R[2, 1] := 2*(q[2]*q[3] + q[1]*q[4]);
      R[2, 2] := q[1]*q[1] + q[3]*q[3] - q[2]*q[2] - q[4]*q[4];
      R[2, 3] := 2*(q[3]*q[4] - q[1]*q[2]);
      R[3, 1] := 2*(q[2]*q[4] - q[1]*q[3]);
      R[3, 2] := 2*(q[3]*q[4] + q[1]*q[2]);
      R[3, 3] := q[1]*q[1] + q[4]*q[4] - q[2]*q[2] - q[3]*q[3];
    end quat2rot;

    function clip
      // inputs
      input Real x;
      // [-] input value
      input Real x_min;
      // [-] minimum limit
      input Real x_max;
      // [-] maximum limit
      // output
      output Real y;
      // [-] clipped value
    algorithm
      y := if x < x_min then x_min else if x > x_max then x_max else x;
    end clip;

    function hatmap
      // input
      input Real v[3];
      // [-] 3D vector
      // output
      output Real V[3, 3];
      // [-] cross-product matrix
    algorithm
      V := [0, -v[3], v[2]; v[3], 0, -v[1]; -v[2], v[1], 0];
    end hatmap;

    function quat2eul
    // note: euler angle represents same rotation as quaternion
      // input
      input Real q[4];            // [-] quaternion
      // output
      output Real eul[3];         // [-] euler angle (3-2-1 rotation)
    algorithm
    
      eul[1] := atan((2*q[3]*q[4]+2*q[1]*q[2])/(2*q[1]^2+2*q[4]^2-1));
      eul[2] := asin(-(2*q[2]*q[4]-2*q[1]*q[3]));
      eul[3] := atan((2*q[2]*q[3]+2*q[1]*q[4])/(2*q[1]^2+2*q[2]^2-1));
      
    end quat2eul;
  end Utils;

  model ExampleHovering
  
    // parameters
    parameter Integer fidelity = 1 "Select fidelity level"
      annotation(choices(choice = 1 "Low-Fidelity", choice = 2 "High-Fidelity"));
      
    Components.Quadrotor quadrotor(fidelity = fidelity) annotation(
      Placement(transformation(origin = {1, 53}, extent = {{-35, -35}, {35, 35}})));
    Components.Controller controller annotation(
      Placement(transformation(origin = {0, -52}, extent = {{-35, -35}, {35, 35}})));
      
    equation
    
    connect(quadrotor.sensor, controller.sensor) annotation(
        Line(points = {{46, 61}, {46, 2}, {47, 2}, {47, -52}}, thickness = 0.5));
    connect(quadrotor.control, controller.control) annotation(
        Line(points = {{-44, 60}, {-44, 3}, {-47, 3}, {-47, -52}}, thickness = 0.5));
    
    annotation(
        Diagram);
      
  end ExampleHovering;
end GSQuad;
