import org.webpki.util.IO;
import org.webpki.util.UTF8;

public class BuildSystem {
  String template;
  String testFileDirectory;
  Integer index;
  static final String TEST = "TESTS = [\n";

  void addFile(String testFileName) {
    String content = UTF8.decode(IO.readFile(testFileDirectory + testFileName));
    content = content.substring(0, content.indexOf("\n") + 1) +
              content.substring(content.indexOf("\n\n") + 1);
    content = content.replace("\\", "\\\\");
    while (true) {
      int i = content.indexOf("\"\"\"");
      if (i < 0) break;
      int j = content.indexOf("\"\"\"", i + 3);
      if (j < 0) throw new RuntimeException("non-matching comments");
      content = content.substring(0, i) + content.substring(j + 3);
    }
    content = "['" + testFileName + "',\n\"\"\"\n" +
              content + "\"\"\"]";
    if (index == null) {
      index = template.indexOf(TEST) + TEST.length();
    } else {
      content = ",\n" + content;
    }
    template = template.substring(0, index) + content + template.substring(index);
    index += content.length();
  }

  BuildSystem(String templateFileName, String testFileName, String testFileDirectory) {
    template = UTF8.decode(IO.readFile(templateFileName));
    this.testFileDirectory = testFileDirectory;
    addFile("arrays.py");
    addFile("maps.py");
    addFile("float.py");
    addFile("integer.py");
    addFile("int-ranges.py");
    addFile("nondeterministic.py");
    addFile("diagnostic.py");
    addFile("check-for-unread.py");
    addFile("sequence.py");
    addFile("clone.py");
    addFile("cotx.py");
    addFile("miscellaneous.py");
    addFile("nesting.py");
    addFile("base64url.py");
    addFile("xyz-encoder.py");
    addFile("xyz-decoder.py");
    IO.writeFile(testFileName, template);
  }
  public static void main(String[] args) {
    new BuildSystem(args[0], args[1], args[2]);
  }
}