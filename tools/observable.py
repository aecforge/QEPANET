class Observable(object):
    def __init__(self):
        self._observers = []

    def attach(self, observer):
        if not observer in self._observers:
            self._observers.append(observer)

    def detach(self, observer):
        try:
            self._observers.remove(observer)
        except ValueError:
            pass

    def notify(self, modifier=None):
        for observer in self._observers:
            if modifier != observer:
                observer.update(self)


class Parameters(Observable):
    def __init__(self):
        super(Parameters, self).__init__()
        self._junctions_vlay = None

    @property
    def junctions_vlay(self):
        return self._junctions_vlay

    @junctions_vlay.setter
    def junctions_vlay(self, value):
        self._junctions_vlay = value
        print 'setto'
        self.notify()


class Gui():
    def update(self, subject):
        print 'notificato'
        print len(subject.junctions_vlay)


# Example usage...
def main():
  params = Parameters()
  gui = Gui()
  params.attach(gui)

  print params.junctions_vlay

  params.junctions_vlay = [10]
  params.detach(gui)

if __name__ == '__main__':
  main()