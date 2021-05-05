import backend.nlu.ability as ablity


def test_asr_carnumber():
    text = "月A幺二三一A"
    obj = ablity.builtin.asr_car_number.AsrCarnumber()
    
