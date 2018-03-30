using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Web.Script.Serialization;

namespace EritePlugins.Core.Purulaatikko
{
    public class JsonReader
    {
        // read python parts in i.e. python-proto\data.json

        public static IList<JsSection> ReadItIn(string FileLoc)
        {
            List<JsSection> parts = null;
            try
            {
                //var ro = new JsRootobject();
                StreamReader sr = new StreamReader(FileLoc);
                string jsonString = sr.ReadToEnd();
                JavaScriptSerializer ser = new JavaScriptSerializer();
                var ro = ser.Deserialize<List<JsSection>>(jsonString);
                parts = ro/*.Property1*/.ToList();
            }
            catch (Exception e)
            {
                System.Diagnostics.Debug.WriteLine($"[ERITE] Json error: {e.Message}");
            }
            return parts;
        }
    }


    //public class JsRootobject
    //{
    //    public JsSection[] Property1 { get; set; }
    //}


    public class JsSection
    {
        public string section { get; set; }
        public JsPart[] parts { get; set; }
        public JsPlane[] planes { get; set; }
        public JsPlane[] fitplanes { get; set; }        
        public JsCoordinateSystem coordinate_system { get; set; }
        public JsCutobject[] cutobjects { get; set; }
        public JsPart[] cutcontours { get; set; }
    }

    public class JsPart
    {
        public string profile { get; set; }
        public int? rotation { get; set; }
        public JsPoint[] points { get; set; }
        public string material { get; set; }
        public int? klass { get; set; }
    }

    public class JsPoint
    {
        public float x { get; set; }
        public float y { get; set; }
        public float z { get; set; }
    }

    public class JsCoordinateSystem
    {
        public JsPoint _origin { get; set; }
        public JsPoint _x_axis { get; set; }
        public JsPoint _y_axis { get; set; }
    }

    public class JsPlane
    {
        public JsPoint point1 { get; set; }
        public JsPoint point2 { get; set; }
        public JsPoint point3 { get; set; }
    }

    public class JsCutobject
    {
        public JsPoint min_point { get; set; }
        public JsPoint max_point { get; set; }
    }

    //---------------------------------------

        /*
    public class Rootobject
    {
        public string section { get; set; }
        public Part[] parts { get; set; }
        public Plane[] planes { get; set; }
        public Coordinate_System coordinate_system { get; set; }
        public Cutobject[] cutobjects { get; set; }
    }

    public class Coordinate_System
    {
        public _Origin _origin { get; set; }
        public _X_Axis _x_axis { get; set; }
        public _Y_Axis _y_axis { get; set; }
    }

    public class _Origin
    {
        public float x { get; set; }
        public float y { get; set; }
        public float z { get; set; }
    }

    public class _X_Axis
    {
        public float x { get; set; }
        public float y { get; set; }
        public float z { get; set; }
    }

    public class _Y_Axis
    {
        public float x { get; set; }
        public float y { get; set; }
        public float z { get; set; }
    }

    public class Part
    {
        public string profile { get; set; }
        public object rotation { get; set; }
        public Point[] points { get; set; }
        public string material { get; set; }
        public int klass { get; set; }
    }

    public class Point
    {
        public float x { get; set; }
        public float y { get; set; }
        public float z { get; set; }
    }

    public class Plane
    {
        public Point1 point1 { get; set; }
        public Point2 point2 { get; set; }
        public Point3 point3 { get; set; }
    }

    public class Point1
    {
        public float x { get; set; }
        public float y { get; set; }
        public float z { get; set; }
    }

    public class Point2
    {
        public float x { get; set; }
        public float y { get; set; }
        public float z { get; set; }
    }

    public class Point3
    {
        public float x { get; set; }
        public float y { get; set; }
        public float z { get; set; }
    }

    public class Cutobject
    {
        public Min_Point min_point { get; set; }
        public Max_Point max_point { get; set; }
    }
    */


}
