import os
import csv
import argparse
from pathlib import Path
from rosbags.highlevel import AnyReader

class RosbagParser:
    """
    A class to parse ROS 2 bag files and export specified topics to CSV files.

    This parser uses the 'rosbags' library, which does not require a local ROS 2
    installation, making it portable. It can handle nested message types by
    flattening them into a single row.
    """

    def __init__(self, bag_file_path: str, output_dir: str = '.'):
        """
        Initializes the RosbagParser.

        Args:
            bag_file_path (str): The full path to the ros2 bag folder
            output_dir (str, optional): The directory to save output CSV files. 
                                        Defaults to the current directory.
        """
        self.bag_path = Path(bag_file_path)
        self.output_dir = output_dir
        self.bag_file_name = self.bag_path.stem
       
        if not self.bag_path.exists():
            raise FileNotFoundError(f"Rosbag path (file or directory) not found at: {self.bag_path}")

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"Created output directory: {self.output_dir}")

    @staticmethod
    def _flatten_message(msg: object, parent_key: str = '') -> dict:
        """
        Recursively flattens a nested message object into a single dictionary.
        This is a helper method to handle complex, nested ROS messages.
        
        Args:
            msg (object): The ROS message object to flatten.
            parent_key (str, optional): The base key for nested fields.
        
        Returns:
            dict: A flattened dictionary representation of the message.
        """
        items = {}
        attrs = [s for s in dir(msg) if not s.startswith('_')]

        for slot in attrs:
            value = getattr(msg, slot)
            new_key = f"{parent_key}.{slot}" if parent_key else slot

            if hasattr(value, '__module__') and 'builtin' not in value.__module__:
                items.update(RosbagParser._flatten_message(value, new_key))
            elif isinstance(value, list):
                items[new_key] = str(value)
            else:
                items[new_key] = value
        return items

    def export_to_csv(self, topics: list = None):
        """
        Reads the rosbag file and exports messages from topics to CSV files.

        Args:
            topics (list, optional): A list of topic names to export. 
                                     If None, all topics in the bag file will be exported.
        """
        print(f"Opening rosbag file: {self.bag_path}")
        with AnyReader([self.bag_path]) as reader:
            
            # If no topics are specified, get all available topics from the bag
            if not topics:
                print("No topics specified. Exporting all available topics.")
                topics = list(reader.topics.keys())
                print(f"Found topics: {topics}")

            for topic_name in topics:
                connections = [c for c in reader.connections if c.topic == topic_name]
                if not connections:
                    print(f"Warning: Topic '{topic_name}' not found in the bag file.")
                    continue

                # Sanitize the topic name for use as a valid filename
                sanitized_topic_name = topic_name.replace('/', '_').lstrip('_')
                output_file_name = f"{self.bag_file_name}_{sanitized_topic_name}.csv"
                output_file_path = os.path.join(self.output_dir, output_file_name)

                print(f"Processing topic: '{topic_name}'")
                
                first_msg = True
                message_count = 0
                writer = None

                with open(output_file_path, 'w', newline='') as csvfile:
                    for connection, timestamp, rawdata in reader.messages(connections=connections):
                        msg = reader.deserialize(rawdata, connection.msgtype)
                        flat_msg = self._flatten_message(msg)

                        if first_msg:
                            # Create header from the keys of the first flattened message
                            header = ['timestamp'] + sorted(flat_msg.keys())
                            writer = csv.DictWriter(csvfile, fieldnames=header, extrasaction='ignore')
                            writer.writeheader()
                            first_msg = False
                        
                        row_data = {'timestamp': timestamp}
                        row_data.update(flat_msg)
                        writer.writerow(row_data)
                        message_count += 1
                
                if message_count > 0:
                    print(f"SUCCESS: Wrote {message_count} messages to {output_file_path}")
                else:
                    print(f"Info: No messages found for topic '{topic_name}'.")
                    os.remove(output_file_path) # Clean up empty file

# --- Main execution block to allow running this file as a standalone script ---
def main():
    """Main function to handle command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract topics from a rosbag file into CSV files without a ROS environment."
    )
    parser.add_argument('bag_file', help="Path to the rosbag file.")
    parser.add_argument(
        '--topics', 
        nargs='+', 
        help="List of topics to extract. If not specified, all topics will be extracted."
    )
    parser.add_argument(
        '--output-dir', 
        dest='output_dir', 
        default='.', 
        help="Directory to save the output CSV files."
    )

    args = parser.parse_args()

    try:
        # Create a parser instance and run the export
        rosbag_parser = RosbagParser(args.bag_file, args.output_dir)
        rosbag_parser.export_to_csv(args.topics)
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    main()