using System;
using EritePlugins.Core.Purulaatikko;
//using Humper;
using SwecoToolbar;
using Tekla.Structures.Geometry3d;
using TSM = Tekla.Structures.Model;

namespace EritePlugins.Core
{
    class TemporaryWorkplane : IDisposable
    {
        private TSM.Model _model;
        private TSM.TransformationPlane _oldPlan;

        public static TemporaryWorkplane FromJsPlane(JsCoordinateSystem coordinateSystem)
        {
            if (null == coordinateSystem) return null;
            var teklaPlane = new TSM.TransformationPlane(coordinateSystem.GetCoordSys());
            return new TemporaryWorkplane(teklaPlane);
        }

        public TemporaryWorkplane(TSM.TransformationPlane planeToWorkOn)
        {
            _model = new TSM.Model();
            // save current plan
            _oldPlan = _model.GetWorkPlaneHandler().GetCurrentTransformationPlane();
            // set workplan
            _model.GetWorkPlaneHandler().SetCurrentTransformationPlane(planeToWorkOn);
            Tracer._trace("Setting new plane to work at.");
        }

        protected virtual void Dispose(bool disposing)
        {
            if (disposing)
            {
                // set back old one
                if (null != _oldPlan)
                {
                    Tracer._trace("Setting work plane back.");
                    _model?.GetWorkPlaneHandler().SetCurrentTransformationPlane(_oldPlan);
                }
                _model = null; _oldPlan = null;
            }
        }

        public void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }
    }

    public class GeometryUtils
    {
        /*
        class Box
        {
           internal double x { get; }
           internal double y { get; }
           internal double width { get; }
           internal double height { get; }
        }

        bool DoBoxesIntersect(Box a, Box b)
        {
            return (Math.Abs(a.x - b.x) * 2 < (a.width + b.width)) &&
                   (Math.Abs(a.y - b.y) * 2 < (a.height + b.height));
        }
        */
        public static bool testAABBAABB(AABB a, AABB b)
        {
            var a_center = a.GetCenterPoint();
            var b_center = b.GetCenterPoint();
            var a_r = new Vector(a.MaxPoint - a_center);
            var b_r = new Vector(b.MaxPoint - b_center);
            if (Math.Abs(a_center.X - b_center.X) > (a_r.X + b_r.X) ) return false;
            if (Math.Abs(a_center.Y - b_center.Y) > (a_r.Y + b_r.Y) ) return false;
            if (Math.Abs(a_center.Z - b_center.Z) > (a_r.Z + b_r.Z) ) return false;
 
            // We have an overlap
            return true;
        }
}

    public static class GeomExtensions
    {
        public static AABB GetAABB(this TSM.Part part)
        {
            var solid = part.GetSolid();
            return new AABB(solid.MinimumPoint, solid.MaximumPoint);
        }

        public static Point GetPoint(this JsPoint jsPoint)
        {
            return new Point
            {
                X = jsPoint.x,
                Y = jsPoint.y,
                Z = jsPoint.z
            };
        }
        public static Vector GetVector(this JsPoint jsPoint)
        {
            return new Vector(jsPoint.GetPoint());
        }

        public static CoordinateSystem GetCoordSys(this JsCoordinateSystem coordinateSystem)
        {
            return new CoordinateSystem
            {
                Origin = coordinateSystem._origin.GetPoint(),
                AxisX = coordinateSystem._x_axis.GetVector(),
                AxisY = coordinateSystem._y_axis.GetVector()
            };
        }
    }
}
