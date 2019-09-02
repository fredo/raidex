from transitions import State, Machine

def manual_on_enter(event):

    print(f'ON ENTER MANUALLY {event.model.state}')

    for name in event.__dict__:
        print(name)
    saved_args = locals()
    print("saved_args is", saved_args)


state = State("test", on_enter=manual_on_enter)


class Model:

    pass


fsm = Machine(states=[state], initial="test", send_event=True)

model = Model()
fsm.add_model(model)
model.to_test()

