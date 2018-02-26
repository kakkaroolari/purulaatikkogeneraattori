using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace EritePlugins.Core.Purulaatikko
{
    internal static class ChainSaw
    {
        internal static Tekla.Structures.Geometry3d.Point ToTS(this JsPoint jsPoint)
        {
            return new Tekla.Structures.Geometry3d.Point(jsPoint.x, jsPoint.y, jsPoint.z);
        }

        internal static Tekla.Structures.Model.Material FromString(string spec)
        {
            Tekla.Structures.Model.Material ts;
            //if (spec.ToLower.Contains("concrete"))
            //{
            ts = new Tekla.Structures.Model.Material
            {
                MaterialString = spec
            };
            //}
            return ts;
        }

        // Not exactly model helper but frak it..
        public static bool IsNullOrEmpty(this IEnumerator source)
        {
            if (source != null)
            {
                while (source.MoveNext())
                {
                    return false;
                }
            }
            return true;
        }
    }
}
