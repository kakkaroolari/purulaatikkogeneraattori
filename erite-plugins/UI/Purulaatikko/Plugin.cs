namespace EritePlugins.UI.Purulaatikko
{
    using Common;
    using Core.Purulaatikko;
    using EritePlugins.Common;
    using System;
    using System.Windows.Forms;
    using System.Collections.Generic;
    using Tekla.Structures.Model;
    using Tekla.Structures.Model.UI;
    using Tekla.Structures.Plugins;

    [Plugin(Consts.PluginNames.GeneratorPluginName)]
    [PluginUserInterface("EritePlugins.UI.Purulaatikko.MainForm")]
    public class Plugin : PluginBase
    {
        private InputHandler _inputHandler;
        private bool _showWarnings;

        public Plugin(StructuresData data)
        {
            try
            {
                _inputHandler = new InputHandler(data);
            }
            catch (Exception exception)
            {
                // ignored
            }
        }




        public override List<InputDefinition> DefineInput()
        {
            var inputList = new List<InputDefinition>();

            try
            {
                var picker = new Picker();

                var pickedPoint = picker.PickPoints(Picker.PickPointEnum.PICK_ONE_POINT, "Pick point");

                if (pickedPoint != null)
                {
                    inputList.Add(new InputDefinition(pickedPoint));
                }

            }
            catch (Exception exception)
            {
                // ignored
            }

            return inputList;
        }

        public override bool Run(List<InputDefinition> input)
        {
            _inputHandler.SetInputObjects(input);

            if (!_inputHandler.IsInputValid)
            {
                return false;
            }

            _inputHandler.SetAttributes();

            var creator = new Creator();

            creator.SetAttributes(_inputHandler.Attributes);
            return creator.Create();
        }


    }
}
