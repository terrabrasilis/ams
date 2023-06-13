var values = [0, 0.35, 0.85, 1];
var slider = document.getElementById("myRange");
var output = document.getElementById("sliderValue");

slider.addEventListener("input", function() {
  var position = Math.round(this.value);
  this.value = position;
  output.innerHTML = values[position];
  console.log("Valor: " + output.innerHTML);
  updateSliderValue(position);
});

// Chamar a função para aplicar estilos iniciais
updateSliderValue(slider.value);

function updateSliderValue(value) {
  var labels = document.querySelectorAll('.tick-label');
  labels.forEach(function (label) {
    label.style.fontWeight = 'normal';
    label.style.fontSize = '11px';
  });

  var selectedLabel = document.querySelector('.tick-label:nth-child(' + (value + 1) + ')');
  selectedLabel.style.fontWeight = 'bold';
  selectedLabel.style.fontSize = '13px';
}
