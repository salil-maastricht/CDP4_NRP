import os
import rospy
from std_msgs.msg import Float64
from cv_bridge import CvBridge, CvBridgeError
from sensor_msgs.msg import Image, JointState
from spiking_saccade_generator.srv import MoveEyes

@nrp.MapRobotSubscriber("image", Topic("/icub/icub_model/left_eye_camera/image_raw", Image))
@nrp.MapRobotSubscriber("joints", Topic("/icub/joints", JointState))
@nrp.MapRobotPublisher("horizontal_eye_pos_pub", Topic("/icub/eye_version/pos", Float64))
@nrp.MapRobotPublisher("vertical_eye_pos_pub", Topic("/icub/eye_tilt/pos", Float64))
@nrp.MapRobotPublisher("right_shoulder_pitch", Topic("icub/r_shoulder_pitch/pos", Float64))
@nrp.MapRobotPublisher("left_shoulder_pitch", Topic("icub/l_shoulder_pitch/pos", Float64))
@nrp.MapRobotPublisher("plotter", Topic("/cdp4/visualizer", Image))
@nrp.MapVariable("initialization", initial_value=None)
@nrp.MapVariable("bridge", initial_value=None)
@nrp.MapVariable("saliency_model", initial_value=None)
@nrp.MapVariable("ts", initial_value=None)
@nrp.MapVariable("np", initial_value=None)
@nrp.MapVariable("tf", initial_value=None)
@nrp.MapVariable("T_SIM", initial_value=5)
@nrp.MapVariable("Nrc", initial_value=48)
@nrp.MapVariable("last_horizontal", initial_value=0)
@nrp.MapVariable("last_vertical", initial_value=0)
@nrp.MapVariable("previous_count", initial_value=[0, 0, 0, 0])
@nrp.MapVariable("saccade_generator", initial_value=rospy.ServiceProxy('/move_eyes', MoveEyes))
@nrp.MapVariable("fig", initial_value=None)
@nrp.MapVariable("plt", initial_value=None)
@nrp.MapVariable("label", initial_value='%s')
@nrp.MapVariable("labels", initial_value=None)
@nrp.MapVariable("eye_positions", initial_value=None)
@nrp.MapVariable("sequence", initial_value='%s')
@nrp.MapVariable("sequences", initial_value=None)
@nrp.MapVariable("dataset_path", initial_value='/home/bbpnrsoa/')
@nrp.MapVariable("global_dataset_counter", initial_value=0)
@nrp.MapVariable("counter", initial_value=1)
@nrp.Robot2Neuron()
def cdp4_loop(t, image, joints, horizontal_eye_pos_pub, vertical_eye_pos_pub, right_shoulder_pitch,
              left_shoulder_pitch, plotter, initialization, bridge, saliency_model, ts, np, tf, T_SIM,
              Nrc, last_horizontal, last_vertical, previous_count, saccade_generator, fig, plt, label,
              labels, eye_positions, sequence, sequences, dataset_path, global_dataset_counter, counter):

    # initialize variables to persist
    if initialization.value is None:

        # Put the icub arms down to avoid having them in the image
        right_shoulder_pitch.send_message(1.0)
        left_shoulder_pitch.send_message(1.0)

        # move the eyes to the center
        horizontal_eye_pos_pub.send_message(0)
        vertical_eye_pos_pub.send_message(0)

        try:
            import os
            import sys
            sys.path.insert(0, '/home/bbpnrsoa/cdp4_venv/lib/python3.8/site-packages')

            import numpy 
            np.value = numpy

            import tensorflow 
            tf.value = tensorflow

            import matplotlib.pyplot
            plt.value = matplotlib.pyplot
            plt.value.switch_backend('Agg')
            fig.value, _ = plt.value.subplots(1, figsize=(6, 6))

            from model_TS import TS

        except:
            clientLogger.info("Unable to import TensorFlow, did you change the path in the transfer function?")
            raise

        n = 48
        N = n ** 2
        PARAMS = {'N': N, 'sigma': 3., 'tau': 1e-4, 'J': [0.001, 8.00, 0.75], 'mu': 35.,
                  'I_ext': np.value.zeros(N), 'freq': 3.}
        bridge.value = CvBridge()

        saliency_model.value = tf.value.saved_model.load(os.path.join(os.environ['HOME'],
                               '.opt/nrpStorage/cdp4_loop_experiment_0/resources/salmodel/'))
        saliency_model.value = saliency_model.value.signatures['serving_default']
        ts.value = TS(PARAMS)

        # Create directory to save data if it doesn't exist
        if 'cdp4_dataset' not in os.listdir(dataset_path.value):
            os.mkdir(dataset_path.value + 'cdp4_dataset')
            labels.value = np.value.array([], dtype=int)
            eye_positions.value = np.value.array([], dtype=float)
            sequences.value = np.value.array([], dtype=int)
        else:
            # Load previous labels list and dataset_counter
            existing_data = os.listdir(dataset_path.value + 'cdp4_dataset')
            existing_data = [e for e in existing_data if 'png' in e]
            global_dataset_counter.value = len(existing_data)
            labels.value = np.value.load(dataset_path.value + 'cdp4_dataset/labels.npy')
            eye_positions.value = np.value.load(dataset_path.value + 'cdp4_dataset/eye_positions.npy')
            sequences.value = np.value.load(dataset_path.value + 'cdp4_dataset/sequences.npy')

        clientLogger.info("Initialization ... Done!")
        initialization.value = True
        return

    if joints.value is not None and image.value is not None:

        import cv2
        from PIL import Image
        cv2_img = bridge.value.imgmsg_to_cv2(image.value, 'rgb8')
        
        horizontal_eye_joint_name = 'eye_version'
        vertical_eye_joint_name = 'eye_tilt'
        horizontal_index = joints.value.name.index(horizontal_eye_joint_name)
        timestamp = (joints.value.header.stamp.secs, joints.value.header.stamp.nsecs)
        vertical_index = joints.value.name.index(vertical_eye_joint_name)
        current_eye_pos = (joints.value.position[horizontal_index],
                           joints.value.position[vertical_index])
        #clientLogger.info(t, current_eye_pos, timestamp)

        # Save current image, eye positions, and label
        if np.value.mod(counter.value, 10) == 0:
            labels_dict = {'bed_room': 0, 'kitchen': 1, 'living_room': 2, 'office': 3}
            labels.value = np.value.append(labels.value, labels_dict[label.value])
            eye_positions.value = np.value.append(eye_positions.value, current_eye_pos)
            sequences.value = np.value.append(sequences.value, int(sequence.value))
            im = Image.fromarray(cv2_img)
            im_name = "{}.png".format(global_dataset_counter.value).zfill(8)
            im.save(dataset_path.value + "cdp4_dataset/" + im_name)
            np.value.save(dataset_path.value + "cdp4_dataset/eye_positions", eye_positions.value)
            np.value.save(dataset_path.value + "cdp4_dataset/labels", labels.value)
            np.value.save(dataset_path.value + "cdp4_dataset/sequences", sequences.value)
            global_dataset_counter.value = global_dataset_counter.value + 1

        # Convert ROS image to CV and resize
        cv2_img = cv2.resize(cv2_img, (320, 320))

        input_img = np.value.expand_dims(cv2_img, 0)
        input_img = tf.value.convert_to_tensor(input_img, dtype='float')
        saliency_map = saliency_model.value(input_img)['out'].numpy().squeeze()

        # plot saliency map
        plt.value.imshow(saliency_map, cmap="gray")
        fig.value.canvas.draw()
        plt.value.tight_layout()

        # convert and publish the image on a ROS topic
        img_data = np.value.fromstring(fig.value.canvas.tostring_rgb(), dtype=np.value.uint8)
        img_data = img_data.reshape(fig.value.canvas.get_width_height()[::-1] + (3,))
        ros_img = bridge.value.cv2_to_imgmsg(img_data, 'rgb8')
        plotter.send_message(ros_img)

        saliency_map = saliency_map.flatten()

        ts.value.I_ext = ts.value.read_saliency_NRP(saliency_map)
        target_selection_result = np.value.mean(ts.value.simulate(T_SIM.value), axis=1)
        target_selection_argmax = np.value.argmax(target_selection_result)
        target_selection_idx = np.value.unravel_index(target_selection_argmax, (48, 48))
        #clientLogger.info("Target Selection Results: {}".format(target_selection_idx))

        from utils import ind2rad
        target_h = ind2rad(target_selection_idx[1])
        target_v = ind2rad(target_selection_idx[0])
        new_vert = current_eye_pos[1] - target_v * 1.13 / 2.0
        new_hori = current_eye_pos[0] - target_h * 1.13 / 2.0

        clientLogger.info("Displacements: {}, {}".format(target_h, target_v))

        #sg_output = saccade_generator.value(0., 1000., target_h, target_v, last_horizontal.value,
        #                                    last_vertical.value, previous_count.value)
        #clientLogger.info(sg_output)

        #horizontal_eye_pos_pub.send_message(sg_output.horizontal + current_eye_pos[0])
        #vertical_eye_pos_pub.send_message(sg_output.vertical + current_eye_pos[1])
        clientLogger.info("Eye Positions: {}, {}".format(current_eye_pos[0], current_eye_pos[1]))

        horizontal_eye_pos_pub.send_message(new_hori)
        vertical_eye_pos_pub.send_message(new_vert)

        #last_horizontal.value = sg_output.horizontal
        #last_vertical.value = sg_output.vertical
        #previous_count.value = sg_output.previous_count_new

        counter.value = counter.value + 1

