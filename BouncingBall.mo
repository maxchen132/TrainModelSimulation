model BouncingBall "bouncing ball"
    constant Real g = 9.81;
    parameter Real c = 0.9;
    parameter Real radius = 0.1;
    Real height(start = 1, fixed = false);
    Real velocity(start = 0, fixed = false);
equation
    der(height) = velocity;
    der(velocity) = -g;
    when height <= radius then
        reinit(velocity, -c*pre(velocity));
    end when;
end BouncingBall;
