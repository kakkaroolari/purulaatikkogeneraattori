using System;
using EritePlugins.Core.Purulaatikko;
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

    public static class GeomExtensions
    {
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
