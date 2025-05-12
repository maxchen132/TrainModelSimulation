model SimpleMotion
  Real x(start=0); // Position
  Real v(start=5); // Velocity
  parameter Real a = -9.81; // Acceleration (e.g., gravity)
equation
  der(x) = v;   // dx/dt = velocity
  der(v) = a;   // dv/dt = acceleration
end SimpleMotion;
