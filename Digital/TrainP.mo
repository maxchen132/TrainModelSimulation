package TrainP
   
model Train
    // Include the world environment
    Modelica.Mechanics.MultiBody.World world annotation(
      Placement(transformation(extent = {{-100, 50}, {-80, 70}})));
    // MultiBody Components
    Modelica.Mechanics.MultiBody.Parts.BodyShape trainBody(r = {0, 0, 0}, m = 1000, I_11 = 500, I_22 = 500, I_33 = 500, shapeType = "box", length = 2, width = 1, height = 1, r_CM = {0, 0, 0}) annotation(
 // Explicitly set r_CM
      Placement(transformation(extent = {{-10, -10}, {10, 10}})));
    // Fixed Track Start
    Modelica.Mechanics.MultiBody.Parts.FixedTranslation trackStart(r = {-10, 0, 0}) annotation(
      Placement(transformation(extent = {{-40, 10}, {-20, 30}})));
    // Fixed Track End
    Modelica.Mechanics.MultiBody.Parts.FixedTranslation trackEnd(r = {10, 0, 0}) annotation(
      Placement(transformation(extent = {{20, 10}, {40, 30}})));
    // Curved Sections of Track
    Modelica.Mechanics.MultiBody.Joints.Revolute curve1(n = {0, 0, 1}, phi(start = 0, fixed = true), w(start = 1)) annotation(
      Placement(transformation(extent = {{-20, -10}, {-10, 0}})));
    Modelica.Mechanics.MultiBody.Joints.Revolute curve2(n = {0, 0, 1}, phi(start = 0, fixed = true), w(start = 1)) annotation(
      Placement(transformation(extent = {{10, -10}, {20, 0}})));
    // Train Controller (Keeps Speed Constant)
    Modelica.Blocks.Continuous.PI speedController(k = 100, T = 0.1) annotation(
      Placement(transformation(extent = {{-40, -40}, {-20, -20}})));
    // Desired Speed Input
    Modelica.Blocks.Sources.Constant speedRef(k = 10) annotation(
      Placement(transformation(extent = {{-80, -40}, {-60, -20}})));
    // Train Force (Motor Effect) - Fixed Equations
    Modelica.Mechanics.Translational.Sources.Force trainForce annotation(
      Placement(transformation(extent = {{0, -40}, {20, -20}})));
    // Dummy Mass to Balance Equations
    Modelica.Mechanics.Translational.Components.Mass trainMass(m = 1000) annotation(
      Placement(transformation(extent = {{30, -40}, {50, -20}})));
  equation
// Connect Speed Reference to Controller
    connect(speedRef.y, speedController.u) annotation(
      Line(points = {{-59, -30}, {-42, -30}}, color = {0, 0, 127}));
// Connect Controller Output to Train Force
    connect(speedController.y, trainForce.f) annotation(
      Line(points = {{-19, -30}, {-1, -30}}, color = {0, 0, 127}));
// Fixing Train Force Balance (to avoid equation imbalance)
    connect(trainForce.flange, trainMass.flange_a) annotation(
      Line(color = {0, 0, 0}));
// Track Connections
    connect(trackStart.frame_b, curve1.frame_a) annotation(
      Line(color = {95, 95, 95}));
    connect(curve1.frame_b, trackEnd.frame_a) annotation(
      Line(color = {95, 95, 95}));
    connect(trackEnd.frame_b, curve2.frame_a) annotation(
      Line(color = {95, 95, 95}));
    connect(curve2.frame_b, trackStart.frame_a) annotation(
      Line(color = {95, 95, 95}));
// Connect Train to Track
    connect(trainBody.frame_a, trackStart.frame_b) annotation(
      Line(color = {95, 95, 95}));
    annotation(
      experiment(StopTime = 20),
      Diagram);
  end Train;

model SimpleTrain
  import Modelica;
  import Modelica.Blocks.Sources;
  import Modelica.Blocks.Continuous;
  import Modelica.Mechanics.MultiBody;
  import Modelica.Mechanics.Translational;
  
  // Parameters (currently placeholder values)
  parameter Real m = 1;    
  parameter Real F = 1;    
  parameter Real b = 0.5;        
  parameter Real R = 0.5;   
  parameter Real L = 1;

  // Motion variables
  Real x(start=0);
  Real v(start=5);
  Real startValue = v / R;
  Real a;             
  Real F_friction;    

  // MultiBody components
  MultiBody.World world;
  MultiBody.Parts.BodyShape trainBody(
    r={0,0,0}, 
    m=m, 
    shapeType="box", 
    length=5, width=2, height=2
  );
  
  MultiBody.Joints.Revolute leftCurve(
    n={0,0,1}, 
    phi(start=0, fixed=true), 
    w(start=startValue)
  );

  MultiBody.Joints.Revolute rightCurve( 
    n={0,0,1},  
    phi(start=0, fixed=true), 
    w(start=startValue)
  );

  MultiBody.Parts.FixedTranslation straight1(r={L, 0, 0});
  MultiBody.Parts.FixedTranslation straight2(r={-L, 0, 0});
  
  //Translational.Sources.Force trainForce;
  //Translational.Components.Mass trainMass(m=m);
  
  //Blocks.Sources.Constant speedRef(k=10);
  //Blocks.Continuous.PI speedController(k=100, T=0.1);

equation
  // Friction force
  F_friction = b * v;
  a = (F - F_friction) / m;

  // Kinematics
  der(x) = v;
  der(v) = a;

  // Track connections
  connect(straight1.frame_b, leftCurve.frame_a);
  connect(leftCurve.frame_b, straight2.frame_a);
  connect(straight2.frame_b, rightCurve.frame_a);
  connect(rightCurve.frame_b, straight1.frame_a);

  // Train movement
  //connect(trainBody.frame_a, straight1.frame_b);
  //connect(trainForce.flange, trainMass.flange_a);

  // Speed control
  //connect(speedRef.y, speedController.u);
  //connect(speedController.y, trainForce.f);

  annotation (experiment(StopTime=20), Diagram);
end SimpleTrain;

  model TestTrain
  equation

  end TestTrain;
end TrainP;
